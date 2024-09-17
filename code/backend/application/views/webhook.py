from flask import Blueprint, request
from flask_restful import *
import json
import requests

# Create a Blueprint for the webhook API
webhook_blueprint = Blueprint('webhook', __name__)
#webhook_api = Api(webhook_blueprint)
#class Webhook(Resource):
@webhook_blueprint.route("/",methods=["POST"],strict_slashes=False)
def webhook():
    # Get the JSON data from the request
    data = request.json
    
    url = "https://chat.googleapis.com/v1/spaces/AAAA7XHBXUM/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=inKFIeet30u4kHP4pykZtKOvLzYmqhAoae6RP-maLL0"

    # Send the webhook request synchronously
        #result = send_webhook(url, data)
    sender = data.get("sender")
    post = data.get("post")
    # Define the message payload
    message = {"text":f"Sender : {sender}\n\nMessage :\n{post}"}
    # Convert the message payload to JSON format
    payload = json.dumps(message)

    # Set the headers
    headers = {
        'Content-Type': 'application/json; charset=UTF-8'
    }
    #print(payload)
    # Send the POST request to the webhook URL
    response = requests.post(url, data=payload, headers=headers)
    #print(response)
    # Check if the message was successfully sent
    if response.status_code == 200:
        return "Message sent successfully!",200
    else:
        return "Failed to send message. Status code:", response.status_code

# Add the Webhook resource to the API with the desired route
#webhook_api.add_resource(Webhook, "/")
