"""
Requires:
pip install flask twilio
"""

# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

# Sample variables to output in SMS
a = int(5)
b = float(7.25)
c = "hello world"


# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.enviro.get("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

# Sends body message. Will automatically be prepended with "Sent from your Twilio trial account - "
message = client.messages.create(
    body= f"Today's weather is sunny with a chance of fruit explosion muffins. This is an integer:{a} This is a float preceeded by a line break {b} \n\n. This is a string {c}",
    from_="+14632783084", # Trial twilio number, do not modify
    to="+16475551234", # SPECIFY PHONE NUMBER OF RECEIVER. ADD +1 COUNTRY CODE.
)

print(message.body)
print(os.environ["TWILIO_ACCOUNT_SID"])
print(os.environ["TWILIO_AUTH_TOKEN"])