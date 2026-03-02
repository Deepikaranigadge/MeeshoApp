# users/sms.py
from django.conf import settings
from twilio.rest import Client

def send_otp_sms(phone_number: str, otp: str) -> None:
    """
    phone_number should include country code, e.g. +91XXXXXXXXXX
    """
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    client.messages.create(
        body=f"Your OTP is {otp}. It is valid for 60 seconds.",
        from_=settings.TWILIO_FROM_NUMBER,
        to=phone_number,
    )
