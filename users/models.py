from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
import random

class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(
        max_length=20,
        choices=(('customer', 'Customer'), ('reseller', 'Reseller')),
        default='customer'
    )

    def __str__(self):
        return self.username
    
from django.db import models
from django.conf import settings

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    house = models.CharField(max_length=255, blank=True, null=True)   # ✅
    area = models.CharField(max_length=255, blank=True, null=True)    # ✅
    pincode = models.CharField(max_length=6, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.city}"

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.user.username


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

# users/models.py

from django.db import models
from django.utils import timezone
import random

class PhoneOTP(models.Model):
    phone_number = models.CharField(max_length=10, unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.is_verified = False
        self.save()

        print(f"✅ OTP for {self.phone_number}: {self.otp}")
        return self.otp

