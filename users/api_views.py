import random
import requests
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from .models import PhoneOTP

FAST2SMS_API_KEY = "YOUR_FAST2SMS_API_KEY"


def send_otp(phone, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "route": "otp",
        "variables_values": otp,
        "numbers": phone
    }
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/json"
    }
    requests.post(url, json=payload, headers=headers)


@api_view(['POST'])
def signup(request):
    phone = request.data.get("phone")

    if not phone:
        return Response({"error": "Phone required"}, status=400)

    otp = str(random.randint(1000, 9999))

    PhoneOTP.objects.create(phone=phone, otp=otp)
    send_otp(phone, otp)

    return Response({"message": "OTP sent"})


@api_view(['POST'])
def verify_otp(request):
    phone = request.data.get("phone")
    otp = request.data.get("otp")

    record = PhoneOTP.objects.filter(phone=phone, otp=otp).first()
    if not record:
        return Response({"error": "Invalid OTP"}, status=400)

    user, _ = User.objects.get_or_create(username=phone)

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh)
    })
