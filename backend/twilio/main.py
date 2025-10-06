"""
Command line tool that takes in a --body and --to argument to send a user-defined SMS (body) to a user-defined phone number (to). Sent from a hardcoded Twilio trial phone number.

Example usage (Windows command prompt):
python twilio.py --body "hello world" --to "+14162345234"
"""

import argparse
import os
from twilio.rest import Client

# Twilio API keys
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

parser = argparse.ArgumentParser()
parser.add_argument("--body", type=str, help="Message to send")
parser.add_argument("--to", type=str, help="Phone number and country code, i.e. +16475551234")

args = parser.parse_args()

# Sends body message. Will automatically be prepended with "Sent from your Twilio trial account - "
message = client.messages.create(
    body = args.body,
    from_="+14632783084", # Trial twilio number, do not modify
    to= args.to
)

# For logging purposes; not necessary for functionality
print(f"Body: {args.body}")
print(f"to: {args.to}")
