
import hashlib
from aiohttp import web
import aiohttp_cors
import logging
import json
import random
import string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from lxml import etree
from lxml.builder import ElementMaker
import asyncio
import json
import time
import ratelimit
import os

from . questions import QuestionBank

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Service:

    RATE_LIMIT_PERIOD = int(os.getenv("RATE_CALL_PERIOD", 60))
    RATE_CALL_LIMIT = int(os.getenv("RATE_CALL_LIMIT", 10))

    def __init__(
            self, verification_secret, from_email, to_email, sendgrid_api_key,
            subject, challenge, questions, port=8080, send=False
    ):

        self.port = port
        self.secret = verification_secret
        self.from_email = from_email
        self.to_email = to_email
        self.sendgrid_api_key = sendgrid_api_key
        self.subject = subject
        self.send_enabled = send
        self.challenge = challenge

        # How long to wait in requests.  This alleviates some low-scale DDoS and
        # fuzzing threats.  Note so important now that the rate limiter is in
        # place.
        self.sleep_time = 0.5

        # How long are challenges valid for?  This is the expiry of challenge
        # validity codes.
        self.response_window = 60

        if challenge:
            with open(questions, "r") as f:
                qdata = json.load(f)

            logging.info(f"Question base of {len(qdata)} loaded")
            
            self.questions = QuestionBank(qdata)

    def make_salt(self):
        return ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(6)
        )

    def generate_signature(self, input):

        salt = self.make_salt()
        value = salt + ":" + input + ":" + self.secret
        hash = hashlib.sha1(value.encode("utf-8"))
        code = hash.hexdigest()
        return salt, code

    def check_signature(self, signature, input):

        key = signature[0]
        code = signature[1]

        value = key + ":" + input + ":" + self.secret

        hash = hashlib.sha1(value.encode("utf-8"))
        if code != hash.hexdigest():
            return False

        return True        

    def generate_expiry(self, valid=0):

        if valid == 0: valid = self.response_window

        expiry = str(int(time.time()) + valid)

        return expiry

    @ratelimit.limits(calls=RATE_CALL_LIMIT, period=RATE_LIMIT_PERIOD)
    def check_expiry(self, validity, valid=0):

        if valid == 0: valid = self.response_window

        now = int(time.time())

        if int(validity) < now:
            return False

        return True

    async def verify(self, request):

        data = await request.json()

        await asyncio.sleep(self.sleep_time)

        try:

            if self.challenge:
                return self.create_challenge(data["email"])
            else:
                return self.create_signature(data["email"])

        except ratelimit.RateLimitException:
            raise web.HTTPTooManyRequests()
        except Exception as e:
            logging.error(str(e))
            raise web.HTTPBadRequest()

    @ratelimit.limits(calls=RATE_CALL_LIMIT, period=RATE_LIMIT_PERIOD)
    def create_challenge(self, email):

        q = self.questions.random_question()
        expiry = self.generate_expiry()

        signature = self.generate_signature(
            expiry + ":" + email + ":" + q.correct
        )


        logging.info(f"Challenge: {q.question}")
        logging.info(f"Expecting: {q.correct}")

        return web.json_response(
            {
                "question": q.question,
                "answers": q.answers,
                "email": email,
                "expiry": expiry,
                "signature": signature,
            },
            status=401
        )

    @ratelimit.limits(calls=RATE_CALL_LIMIT, period=RATE_LIMIT_PERIOD)
    def create_signature(self, email):

        expiry = self.generate_expiry()

        signature = self.generate_signature(expiry + ":" + email)

        logging.info("Verification complete for " + email)

        return web.json_response(
            {
                "email": email,
                "expiry": expiry,
                "signature": signature,
            }
        )
        
    async def response(self, request):

        data = await request.json()

        await asyncio.sleep(self.sleep_time)

        expiry = data["expiry"]

        try:
            if not self.check_expiry(expiry):
                logging.info("Answer timed out")
                return web.HTTPGone()
        except ratelimit.RateLimitException:
            raise web.HTTPTooManyRequests()

        email = data["email"]
        response = data["response"]
        signature = data["signature"]

        logging.info(f"Response: {response}")

        if not self.check_signature(
                signature, expiry + ":" + email + ":" + response
        ):
            return web.HTTPUnauthorized()

        return self.create_signature(email)

    async def submit(self, request):
            
        data = await request.json()

        await asyncio.sleep(self.sleep_time)

        try:

            email = data["email"]
            name = data["name"]
            message = data["message"]
            signature = data["signature"]
            expiry = data["expiry"]

            if not self.check_expiry(expiry):
                logging.info("Answer timed out")
                return web.HTTPGone()

            if not self.check_signature(signature, expiry + ":" + email):
                return web.HTTPUnauthorized()

            logging.info(f"Email: {email}")
            logging.info(f"Name: {name}")
            logging.info(f"Message: {message}")
            logging.info("--------------")

        except ratelimit.RateLimitException:
            raise web.HTTPTooManyRequests()

        except Exception as e:
            logging.error(str(e))
            raise web.HTTPBadRequest()

        M = ElementMaker()

        html = M.div(
            M.p(
                "There has been a ",
                M.strong("New Contact"),
                " from the contact form:"
            ),
            M.p(
                M.table(
                    M.tr(
                        M.td("Name:"),
                        M.td(name),
                    ),
                    M.tr(
                        M.td("Email:"),
                        M.td(email),
                    ),
                    M.tr(
                        M.td("Message:"),
                        M.td(message),
                    ),
                ),
            ),
            M.p("Sent by the Contact service.")
        )

        content = etree.tostring(
            html, xml_declaration=False, encoding="utf-8", standalone=True,
            method='html', pretty_print=False,
        ).decode("utf-8")

        logging.info(str(content))

        if not self.send_enabled:
            logging.warning("Submission is not enabled!")
            return web.Response()

        message = Mail(
            from_email = self.from_email,
            to_emails = self.to_email,
            subject = self.subject,
            html_content = content
        )

        try:

            sg = SendGridAPIClient(self.sendgrid_api_key)

            response = sg.send(message)
            if response.status_code < 200 or response.status_code > 299:
                logging.error(response.status_code)
                logging.error(str(response.body))
                logging.error(str(response.headers))
                return web.HTTPInternalServerError()

            logging.info("Submission was successful!")

        except Exception as e:
            logging.error(str(e))
            raise web.HTTPInternalServerError()

        return web.Response()

        return web.Response(
            headers={
            }
        )

    async def status(self, request):

        await asyncio.sleep(self.sleep_time)

        return web.Response()

    async def task(self):

        app = web.Application()
        
        cors = aiohttp_cors.setup(app)

        resource = cors.add(app.router.add_resource("/api/verify"))
        route = cors.add(
            resource.add_route("POST", self.verify),
            {
                "*": aiohttp_cors.ResourceOptions(allow_credentials=False),
            }
        )

        resource = cors.add(app.router.add_resource("/api/response"))
        route = cors.add(
            resource.add_route("POST", self.response),
            {
                "*": aiohttp_cors.ResourceOptions(allow_credentials=False),
            }
        )

        resource = cors.add(app.router.add_resource("/api/submit"))
        route = cors.add(
            resource.add_route("POST", self.submit),
            {
                "*": aiohttp_cors.ResourceOptions(allow_credentials=False),
            }
        )

        resource = cors.add(app.router.add_resource("/api/status"))
        route = cors.add(
            resource.add_route("GET", self.status),
            {
                "*": aiohttp_cors.ResourceOptions(allow_credentials=False),
            }
        )

        return app

    def run(self):

        web.run_app(self.task(), port=self.port)

