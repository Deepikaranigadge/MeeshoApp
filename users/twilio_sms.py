from twilio.rest import Client
from django.conf import settings

def send_otp(phone_e164):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID) \
        .verifications.create(to=phone_e164, channel="sms")
    
def check_otp(phone_e164, code):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    res = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID) \
        .verification_checks.create(to=phone_e164, code=code)
    return res.status == "approved"    