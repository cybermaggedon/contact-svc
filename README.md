
# Back-end contact service used to power a 'Contact Us' form

This is for people who want a 'contact us' form on a budget.  The commercial
form services are fine but a bit pricey for smaller businesses and startups who
aren't ready for the commercial pricing yet.

This uses the Sendgrid email service, which has a free service level (currently
100 emails per day).  Needs appropriate front-end JavaScript code for the
interactions to work.  Some sample web site code is in the example-web directory.

With this service the client-side code is yours so you can easily style it
to fit in with the rest of the application.

## Architecture

The code here is a service which runs as a back-end.  It has a public API which
can be accessed from the browser client which runs the 'contact us' form.

The service is deployed with a Sendgrid API secret so that it can send emails
through sendgrid.

Browser client code is used to collect information from the user and post to the
back-end.

The service uses open CORS headers so that it can be accessed from anywhere on the
web.  It is inherently open to abuse, and we have a few features which
lower the attack surface to discourage e.g. DDoS, and also complicate life for
the random bots wandering the 'net.

## Security features

- Two-stage submission which involves the exchange of a verification code.
  Makes it a little harder for bots to just spam the submission endpoint.
- An optional challenge step which requires the user to answer a question.
- A delay in the verification steps as a DDoS/fuzz defence.

There is probably enough defence to prevent the worst spambots from spamming you
and using up all your Sendgrid credits, for a small business / hobbyist site.
For anything serious just go and use a commercial form site.

## Workflows

There are two workflows, depending on whether the 'quiz' challenge is turned
on or not:

### Challenge enabled

- Client has 3 values: an email, a name and a message from the form.
- Client calls the 'code' endpoint to generate a code.
- The endpoint returns a 401 (Unauthorized) response indicating the challenge
  workflow is in use.  The response contains a question, and multiple-choice
  answers.
- The user selects an answer.
- client calls the 'response' endpoint with the answer plus the email
  address.
- If the answer is correct, the endpoint returns credentials which are tied
  to the email address.  (if not, a 401 error is returned).
- The client submits name, email and message along with the credentials which
  demonstrate that the verification step was completed.

### Challenge disabled

Like above, but without the challenge step

- Client has 3 values: an email, a name and a message from the form.
- Client calls the 'code' endpoint to generate a code.
- The endpoint returns a 200 response containing the credentials.
- The client submits name, email and message along with the credentials which
  demonstrate that the verification step was completed.

## APIs

### Endpoint: `/api/status`

Purpose: Returns a 200 OK response

Input: n/a

### Endpoint: `/api/code`

Purpose: Generates a validation code 

Input: JSON body containing:
- email

Outputs (challenge workflow): 401 status
- question
- candidate answer list
- Challenge key/code pair

Outputs (non-challenge workflow): 200 status
- Verification key/code pair

### Endpoint: `/api/response`

Purpose: Generates a validation code

Input: JSON body containing:
- answer
- email address
- Challenge key/code pair

Outputs:
- Verification key/code pair

### Endpoint: `/api/submit`

Purpose: Submits the form

Input: JSON body containing:
- name
- email
- message
- Verification key/code pair

Outputs:
- Verification key/code pair

## Usage

```
usage: contact-svc [-h] [--port PORT]
                   [--verification-secret VERIFICATION_SECRET]
                   [--sendgrid-api-key SENDGRID_API_KEY]
                   [--from-email FROM_EMAIL] [--to-email TO_EMAIL]
                   [--subject SUBJECT] [--enable-send] [--enable-quiz]

Back-end for a contact form

options:
  -h, --help            show this help message and exit
  --port PORT, -p PORT  Web service port number
  --verification-secret VERIFICATION_SECRET, -v VERIFICATION_SECRET
                        Verification secret, used to defeat bots
  --sendgrid-api-key SENDGRID_API_KEY, -k SENDGRID_API_KEY
                        Sendgrid API key
  --from-email FROM_EMAIL, -f FROM_EMAIL
                        From email address
  --to-email TO_EMAIL, -t TO_EMAIL
                        To email address
  --subject SUBJECT, -s SUBJECT
                        Email subject header
  --enable-send, -e     Enable Sendgrid email send (default: off)
  --enable-quiz, -q     Enable a little question challenge (default: off)
  --questions QUESTIONS, -Q QUESTIONS
                        JSON file containing quiz questions
```

Configuration parameters:
- Port number: The port number to run the service on, default 8080.
- Verification secret: Used to sign key/code credentials, can be any random
  string.  Should be the same on all services if you use multiple.
  This can also be provided in the VERIFICATION_SECRET environment variable.  
- Sendgrid API key: You get this from the Sendgrid console.  This can also
  be provided in the SENDGRID_API_KEY environment variable.
- From email: The email address that appears in the From: field.  You have to
  configure this into the sendgrid console.
- To email: The email address that appears in the to To: field and receives
  the email.
- Subject: Goes in the email Subject: field.
- Enable send: You have to set this if you want it to work.  Default is off,
  information appears in the log/output, but no output otherwise.
- Enable quiz: Turns on the challenge flow.  The user has to answer a question
  to get the submission to work.
- Questions: JSON file containing quiz questions.  There's 22 questions in
  questions.json, you can add your own.

# Running it

Just run the `contact-svc` script:

```
export PYTHONPATH=.
scripts/contact-svc
```

# Packaging and deployment

The Makefile and Containerfile can be used to build a runnable container.

```
make
```

The Pulumi directory contains a Pulumi deployment which deploys the
contact-svc into Cloud Run on Google Cloud.  You need to tweak a load of
configuration for your environment.

# Licence

Copyright 2024 Cybermaggedon

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

