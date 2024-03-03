
// ContactForm class, provides support and state for the contact form
class ContactForm {

    // form = the HTML DOM element for the form, should have email, name
    // and message fields.  ContactForm changes the submit event.
    // response = a div to put messages in
    // api = The URL of the contact-svc e.g. http://locahost:8080/api
    constructor(form, response, api, fallback) {

        this.form = form;
        this.response = response;
        this.api = api;
        this.fallback = fallback;

        // Jack into the form submit event
        form.addEventListener(
            "submit",
            elt => this.formSubmit(elt)
        );

        this.checkStatus();

    }

    // Status check, 
    checkStatus() {
        console.log("Checking contact-svc backend status...");
        fetch(
            this.api + "/status", { method: "GET", }
        ).then(
            
            resp => {

                if (resp.status == 200) {
                    this.clearStatus();
                    console.log("The contact-svc backend is working.");
                } else if (resp.status == 401) {
                    this.showDown();
                } else {
                    this.showDown();
                }
            }
        ).catch(
            e => {
                console.log("Error: ", e);
                this.showDown();
            }
        );
    }

    // Show an error message
    showError(error) {
        var elt = this.clearStatus();
        elt.appendChild(document.createTextNode(error.toString()));
        elt.classList = "failure";
    }

    // Clear the response DIV
    clearStatus() {
        var elt = this.response;
        while (elt.firstChild)
            elt.removeChild(elt.firstChild);
        elt.classList = "";
        return elt;
    }

    // Show a message with 'OK' styling.
    showOK(msg) {
        var elt = this.clearStatus();
        elt.appendChild(
            document.createTextNode(msg)
        );
        elt.classList = "success";
    }

    // Show that the form has been submitted
    showSubmitted() {
        this.showOK(
            "Your message has been received, we'll be in touch soon."
        );
    }

    // Transitory submitting state
    showSubmitting() {
        this.showOK(
            "Submitting...."
        );
    }

    // Show submission error
    showSubmissionError() {
        this.showError(
            "Submission failed, contact service returned error."
        );
    }

    // Show a challenge error i.e. you answered the question wrong
    showChallengeError() {
        this.showError(
            "Challenge failed."
        );
    }

    // Status check fail means the service is probably offline, show
    // a backup contact method
    showDown() {
        this.showError(this.fallback);
    }

    update_ticker() {
        while (this.countdown.firstChild)
            this.countdown.removeChild(this.countdown.firstChild);
        const now = Math.round(new Date().getTime() / 1000);
        const remaining = (this.expiry - now).toString();

        this.countdown.appendChild(
            document.createTextNode(remaining)
        );

        this.countdown.appendChild(
            document.createTextNode(" second")
        );

        if (remaining != 1)
            this.countdown.appendChild(
                document.createTextNode("s")
            );

    }

    tick() {

        // Submission happened, not ticking now.
        if (this.expiry == 0) return;

        const now = Math.round(new Date().getTime() / 1000);

        if (this.expiry > now) {
            this.update_ticker();
            setTimeout(() => this.tick(), 5000);
        } else {
            this.showError("Challenge has timed out!  Please resubmit.")
            this.expiry = 0;
        }

    }

    // Show a challenge question + buttons
    showChallenge(challenge, email, message, name) {

        // Clear status and configure for buttons
        var elt = this.clearStatus();	
        elt.classList = "challenge";

        let div = document.createElement("div");
        elt.appendChild(div);

        // H2 title
        const h2 = document.createElement("h2");
        div.appendChild(h2);
        h2.appendChild(
            document.createTextNode("Challenge!")
        );

        // prompt
        let p = document.createElement("p");
        div.appendChild(p);
        p.appendChild(
            document.createTextNode("Please answer this question in ")
        );

        let span = document.createElement("span");
        span.id = "countdown";
        span.appendChild(
            document.createTextNode("-")
        );
        p.appendChild(span);
        p.appendChild(document.createTextNode("..."));

        this.countdown = span;

        this.expiry = Number(challenge.expiry);
        setTimeout(() => this.tick(), 5000);

        // Show the question which must be answered
        p = document.createElement("p");
        p.classList = "question";
        div.appendChild(p);
        p.appendChild(
            document.createTextNode(challenge.question)
        );

        const buttons = document.createElement("div");
        buttons.classList = "button-space";
        div.appendChild(buttons);

        // Show possible answers
        for (const a of challenge.answers) {

            let btn = document.createElement("button");
            btn.classList = "button";
            buttons.appendChild(btn);

            btn.appendChild(document.createTextNode(a));

            btn.onclick = (e) => {
                this.respond(
                    a, challenge, email, message, name
                );
            };

        }

        this.update_ticker();

    }

    // Respond to a challenge with an answer
    respond(a, challenge, email, message, name) {

        this.expiry = 0;
        this.countdown = null;

        this.showOK("Sending response...");

        // Send to response API
        fetch(
            this.api + "/response",
            {
                method: "POST",
                body: JSON.stringify({
                    "email": email,
                    "response": a,
                    "signature": challenge.signature,
                    "expiry": challenge.expiry,
                }),
            }
        ).then(
            resp => {
                if (resp.status == 200) {

                    // 200 status = OK.  Decode JSON response...
                    resp.json().then(

                        // ... and use the auth info to submit contact information
                        auth => {
                            this.submit(email, message, name, auth);
                        }

                    );

                } else if (resp.status == 410) {
                    this.showError("Challenge timed out, please try again");
                } else {
                    this.showChallengeError();
                }
            }
        ).catch(
            err => this.showError(err)
        );

    }

    // Submit a contact request, having verified to get a key/code
    submit(email, message, name, resp) {
        
        const submission = {
            "email": email,
            "message": message,
            "name": name,
            "signature": resp.signature,
            "expiry": resp.expiry,
        };
        
        this.showSubmitting();

        // Post to the 'submit' endpoint
        fetch(
            this.api + "/submit",
            {
                method: "POST",
                body: JSON.stringify(submission),
            }
        ).then(
            resp => {

                // Check on status code, 200 == OK.
                if (resp.status == 200) {

                    // Response, also reset form fields now that the submission
                    // worked.
                    this.showSubmitted();
                    this.form.reset();

                } else

                    this.showSubmissionError();

            }
        ).catch(
            err => this.showError(err)
        );

    }

    // Form submit event, this kicks the workflow off
    formSubmit(e) {

        e.preventDefault();

        // Get entered values
        const email = e.target.email.value;
        const message = e.target.message.value;
        const name = e.target.name.value;

        this.clearStatus();

        // Validate fields have enough information (mainly to prevent
        // accidental submission)
        if (!/@/.test(email)) {
            this.showError("Email address is not valid.");
            return;
        }

        if (!/\./.test(email)) {
            this.showError("Email address is not valid.");
            return;
        }

        if (name == "") {
            this.showError("Name is not valid.");
            return;
        }

        if (message == "") {
            this.showError("Message is not valid.");
            return;
        }

        this.showSubmitting();

        // Send to verification endpoint
        fetch(
            this.api + "/verify",
            {
                method: "POST",
                body: JSON.stringify({
                    "email": email
                }),
                headers: {
                    "Accept": "application/json",
                },
            }
        ).then(
            
            resp => {
                
                if (resp.status == 200) {

                    // 200 status, should get signature, go straight to
                    // submission
                    resp.json().then(
                        resp => this.submit(email, message, name, resp)
                    );
                    
                } else if (resp.status == 401) {

                    // 401 status == challenge workflow.  Decode JSON and...
                    resp.json().then(

                        // ... show challenge
                        cha => this.showChallenge(cha, email, message, name)

                    );
                } else {

                    // None of the above, it's an error
                    this.showSubmissionError();
                }
                
            }
            
        ).catch(
            e => {
                console.log("Error: ", e);
                this.showError(e);
            }
        );
        
    }

};

function initContact(form, response, api, fallback) {
    const cf = new ContactForm(form, response, api, fallback);
}

export { initContact };


