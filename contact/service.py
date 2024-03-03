
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

from . questions import QuestionBank

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Service:
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
        # fuzzing threats
        self.sleep_time = 1

        # How long are challenges valid for?  This is the expiry of challenge
        # validity codes
        self.response_window = 45

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

    def generate_validity(self, valid=0):

        if valid == 0: valid = self.response_window

        expiry = str(int(time.time()) + valid)
        sig = self.generate_signature(expiry)

        return expiry, sig

    def check_validity(self, validity, valid=0):

        if valid == 0: valid = self.response_window

        now = int(time.time())

        if int(validity[0]) < now:
            return False

        return self.check_signature(validity[1], validity[0])

    def create_challenge(self):

        q = self.questions.random_question()

        signature = self.generate_signature(q.correct)

        validity = self.generate_validity()

        logging.info(f"Challenge: {q.question}")
        logging.info(f"Expecting: {q.correct}")

        return web.json_response(
            {
                "question": q.question,
                "answers": q.answers,
                "signature": signature,
                "validity": validity
            },
            status=401
        )

    def create_signature(self, email):

        signature = self.generate_signature(email)
        validity = self.generate_validity()

        logging.info("Verification complete for " + email)

        return web.json_response(
            {
                "signature": signature,
                "validity": validity,
            }
        )
        
    async def verify(self, request):

        data = await request.json()

        await asyncio.sleep(self.sleep_time)

        try:

            if self.challenge:
                return self.create_challenge()
            else:
                return self.create_signature(data["email"])

        except Exception as e:
            logging.error(str(e))
            raise web.HTTPBadRequest()

    async def response(self, request):

        data = await request.json()

        await asyncio.sleep(self.sleep_time)

        validity = data["validity"]

        if not self.check_validity(validity):
            logging.info("Answer timed out")
            return web.HTTPGone()

        email = data["email"]
        response = data["response"]
        signature = data["signature"]

        logging.info(f"Response: {response}")

        if not self.check_signature(signature, response):
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
            validity = data["validity"]

            if not self.check_validity(validity):
                logging.info("Answer timed out")
                return web.HTTPGone()

            if not self.check_signature(signature, email):
                return web.HTTPUnauthorized()

            logging.info(f"Email: {email}")
            logging.info(f"Name: {name}")
            logging.info(f"Message: {message}")
            logging.info("--------------")

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

    def run(self):

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

        web.run_app(app, port=self.port)

