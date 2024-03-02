
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
        self.response_window = 120

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

    def generate_code(self, input):

        salt = self.make_salt()
        value = salt + ":" + input + ":" + self.secret
        hash = hashlib.sha1(value.encode("utf-8"))
        code = hash.hexdigest()
        return salt, code

    def check_code(self, verifier, input):

        key = verifier[0]
        code = verifier[1]

        value = key + ":" + input + ":" + self.secret

        hash = hashlib.sha1(value.encode("utf-8"))
        if code != hash.hexdigest():
            return False

        return True        

    def generate_validity_code(self, valid=0):

        if valid == 0: valid = self.response_window

        salt = self.make_salt()
        expiry = str(int(time.time()) + valid)
        value = salt + ":" + expiry + ":" + self.secret
        hash = hashlib.sha1(value.encode("utf-8"))
        code = hash.hexdigest()
        return expiry, salt, code

    def check_validity_code(self, validity, valid=0):

        if valid == 0: valid = self.response_window

        expiry = int(validity[0])
        salt = validity[1]
        code = validity[2]

        now = int(time.time())

        if expiry < now:
            return False

        value = salt + ":" + validity[0] + ":" + self.secret
        hash = hashlib.sha1(value.encode("utf-8"))
        if code != hash.hexdigest():
            return False

        return True        

    async def submission_code(self, request):

        data = await request.json()

        await asyncio.sleep(self.sleep_time)

        try:

            if self.challenge:

                q = self.questions.random_question()

                verifier = self.generate_code(q.correct)

                validity = self.generate_validity_code()

                logging.info(f"Challenge: {q.question}")
                logging.info(f"Expecting: {q.correct}")

                return web.json_response(
                    {
                        "question": q.question,
                        "answers": q.answers,
                        "verifier": verifier,
                        "validity": validity
                    },
                    status=401
                )

            else:
                
                email = data["email"]
                verifier = self.generate_code(email)
                logging.info("Verification complete for " + email)

                return web.json_response(
                    {
                        "verifier": verifier,
                    }
                )

        except Exception as e:
            logging.error(str(e))
            raise web.HTTPBadRequest()

    async def response(self, request):

        data = await request.json()

        await asyncio.sleep(self.sleep_time)

        email = data["email"]
        response = data["response"]
        verifier = data["verifier"]
        validity = data["validity"]

        logging.info(f"Response: {response}")

        if not self.check_code(verifier, response):
            return web.HTTPUnauthorized()

        if not self.check_validity_code(validity):
            logging.info("Answer timed out")
            return web.HTTPGone()

        verifier = self.generate_code(email)

        return web.json_response(
            {
                "verifier": verifier,
            }
        )

    async def submit(self, request):
            
        data = await request.json()

        await asyncio.sleep(self.sleep_time)

        try:

            email = data["email"]
            name = data["name"]
            message = data["message"]
            verifier = data["verifier"]

            logging.info(f"Email: {email}")
            logging.info(f"Name: {name}")
            logging.info(f"Message: {message}")
            logging.info(f"Verifier: {verifier}")
            logging.info("--------------")

            if not self.check_code(verifier, email):
                return web.HTTPUnauthorized()

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

        resource = cors.add(app.router.add_resource("/api/code"))
        route = cors.add(
            resource.add_route("POST", self.submission_code),
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

        resource = cors.add(app.router.add_resource("/api/response"))
        route = cors.add(
            resource.add_route("POST", self.response),
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

