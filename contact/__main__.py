import argparse
import logging
import sys
import signal
import os

from .service import Service

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("contact-svc")
logger.setLevel(logging.INFO)

def run():

    logger.info("Starting...")

    parser = argparse.ArgumentParser(
        prog="contact-svc", description="Back-end for a contact form"
    )

    parser.add_argument(
        "--port", "-p",
        default=8080,
        help="Web service port number"
    )

    parser.add_argument(
        "--verification-secret", "-v",
        default=os.getenv("VERIFICATION_SECRET", "alskfualu").strip(),
        help="Verification secret, used to defeat bots"
    )

    parser.add_argument(
        "--sendgrid-api-key", "-k",
        default=os.getenv("SENDGRID_API_KEY", ""),
        help="Sendgrid API key",
    )

    parser.add_argument(
        "--from-email", "-f",
        default="test@example.com",
        help="From email address",
    )

    parser.add_argument(
        "--to-email", "-t",
        default="test@example.com",
        help="To email address",
    )

    parser.add_argument(
        "--subject", "-s",
        default='New contact',
        help="Email subject header",
    )

    parser.add_argument(
        "--enable-send", "-e",
        default=False,
        action='store_const', const=True,
        help="Enable Sendgrid email send (default: off)", dest='send',
    )

    parser.add_argument(
        "--enable-quiz", "-q",
        default=False,
        action='store_const', const=True,
        help="Enable a little question challenge (default: off)",
        dest='challenge',
    )

    args = parser.parse_args()

    app = Service(
        port=args.port,
        verification_secret=args.verification_secret,
        sendgrid_api_key=args.sendgrid_api_key,
        send=args.send,
        from_email=args.from_email,
        to_email=args.to_email,
        subject=args.subject,
        challenge=args.challenge,
    )

    logger.info("Running service...")

    app.run()

def shutdown_handler(signal, frame):
    logger.info("Signal received, shutting down.")
    logger.info("Exiting.")
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

if __name__ == "__main__":
    run()

