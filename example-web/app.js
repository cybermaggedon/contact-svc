
// Sample setup for contact-svc

// Import module
import { initContact } from './contact-svc.js';

// Set the API URL
const api = "http://localhost:8080/api";

// Initialise the form
initContact(
    document.getElementById("form"),
    document.getElementById("response"),
    api
);

