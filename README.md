# OTS : Online Ticketing System with Discourse Integration

This is an online platform where one can raise their query in form of ticket and support team related to that will resolve the query. Also, the student can take help from discourse community linked with the student account.
**The Admin**, Validate different users, and Create FAQs.

## the features:
* Login/Signup
* Create Ticket
* Edit/Delete Ticket
* High Priority TIcket will be directly sent to G-chat directly using webhook integration.
* User Deletion/Updation
  
## what problem is it solving.

1. Earlier this app's query is only solved and replied by support only but now can be helped by community.
2. High Priority ticket was sent on G-Chat/G-space instead of mail.
    
## Instructions to setup codebase locally

## Instructions to run the code for linux

Currently, the system is locally hosted. The bash files to run it locally are present in the directory.
There are five steps to run the program:
1. Open five terminals and run source venv/bin/activate to start the virtual environment.
2. Then, executes the backend.sh file to start the backend at http://localhost:5000.
3. Then, executes the backend_discourse.sh file to start the discourse backend at http://localhost:3000.
4. Then, executes the frontend.sh file to start the frontend at http://localhost:8080.
5. Then, executes the discourse_frontend.sh file to start the discourse frontend at http://localhost:4200.
Finally, visit the ‘http://127.0.0.1:8080/home’ page on the browser.

## Future Scopes for improvement

1. UI can become better.
2. ML models can be used to create FAQs and setting up high priority.
