from twilio.rest import Client
from django.conf import settings

def send_otp_sms(phone):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
        to=f"+91{phone}",
        channel="sms"
    )