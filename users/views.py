from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import PhoneOTP
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken


from product.models import Product   # use correct app name where Product exists
def home(request):
    products = Product.objects.all()
    return render(request, "index.html", {"products": products})

def register(request):
    return render(request, "users/register.html")

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from .models import PhoneOTP

def login_view(request):
    if request.method == "POST":
        phone = request.POST.get("phone_number")

        # create/get otp row
        obj, created = PhoneOTP.objects.get_or_create(phone_number=phone)
        otp = obj.generate_otp()     # generates and saves OTP

        # store phone in session (for verify step)
        request.session["login_phone"] = phone

        # redirect to otp page
        return redirect("verify_otp")

    return render(request, "users/login.html")


@login_required
def profile(request):
    return render(request, "users/profile.html")


@login_required
def orders(request):
    return render(request, "users/orders.html")

#def logout_view(request):
 #   logout(request)
 #   return redirect("/") 
def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("home") 

# users/views.py
from .utils import send_otp_sms

def signup(request):
    if request.method == "POST":
        phone = request.POST.get("phone_number")

        send_otp_sms(phone)                 # ✅ sends SMS OTP
        request.session["login_phone"] = phone
        return redirect("verify_otp")        # ✅ goes to OTP page

    return render(request, "signup.html")

# users/views.py
from twilio.rest import Client
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.shortcuts import render, redirect

def verify_otp(request):
    phone = request.session.get("login_phone")
    if not phone:
        messages.error(request, "Session expired. Please try again.")
        return redirect("signup")

    if request.method == "POST":
        otp_entered = (
            request.POST.get("otp1","") +
            request.POST.get("otp2","") +
            request.POST.get("otp3","") +
            request.POST.get("otp4","") +
            request.POST.get("otp5","") +
            request.POST.get("otp6","")
        )

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        try:
            result = client.verify.v2.services(
                settings.TWILIO_VERIFY_SERVICE_SID
            ).verification_checks.create(
                to=f"+91{phone}",
                code=otp_entered
            )
        except Exception as e:
            messages.error(request, f"OTP verification failed: {e}")
            return redirect("verify_otp")

        if result.status != "approved":
            messages.error(request, "Enter a correct otp.")
            return redirect("verify_otp")

        # ✅ login user
        User = get_user_model()
        user, _ = User.objects.get_or_create(username=phone)
        login(request, user)

        request.session.pop("login_phone", None)
        messages.success(request, "Logged in successfully")
        return redirect("home")

    # ✅ GET request: show OTP page
    return render(request, "otp.html", {
        "phone_number": phone,
        "is_expired": False,
        "remaining_seconds": 60,
    })

from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import jwt
from django.conf import settings
from .models import PhoneOTP

OTP_EXP_SECONDS = 60

def resend_otp(request):
    otp_token = request.session.get("otp_token")
    phone = None

    # If old token exists, try to extract phone even if expired (optional)
    if otp_token:
        try:
            data = jwt.decode(otp_token, settings.SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
            phone = data.get("phone")
        except Exception:
            phone = None

    if not phone:
        messages.error(request, "Session expired. Please try again.")
        return redirect("signup")

    phone_obj, _ = PhoneOTP.objects.get_or_create(phone_number=phone)
    phone_obj.generate_otp()  # prints new OTP

    # new token (new expiry)
    new_payload = {
        "phone": phone,
        "exp": timezone.now() + timedelta(seconds=OTP_EXP_SECONDS),
        "type": "otp"
    }
    request.session["otp_token"] = jwt.encode(new_payload, settings.SECRET_KEY, algorithm="HS256")

    messages.success(request, "New OTP sent!")
    return redirect("verify_otp")


def otp_page(request):
    return render(request, "otp.html")

def address_page(request):
    return render(request, 'address.html')

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Address

@login_required
def add_address(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        house = request.POST.get("house")
        area = request.POST.get("area")
        city = request.POST.get("city")
        state = request.POST.get("state")
        pincode = request.POST.get("pincode")
        landmark = request.POST.get("landmark", "")

        addr = Address.objects.create(
            user=request.user,
            name=name,
            phone=phone,
            house=house,
            area=area,
            city=city,
            state=state,
            pincode=pincode,
            landmark=landmark,
        )

        # ✅ ADD THESE LINES HERE (after save)
        next_url = request.POST.get("next")
        if next_url:
            return redirect(next_url)

        return redirect("address_list")  # fallback if next not present

    return render(request, "add_address.html")


from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Address
from cart.models import CartItem   # ✅ change app name if different

@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)

    # ✅ SAME as cart_page (DB cart)
    items = CartItem.objects.select_related("product").filter(user=request.user)

    total_items = 0
    total_price = Decimal("0.00")

    for item in items:
        product = item.product
        qty = int(item.qty)

        line_total = Decimal(str(product.price)) * Decimal(qty)
        total_price += line_total
        total_items += qty

    total_discount = Decimal("0.00")
    order_total = total_price - total_discount

    return render(request, "address.html", {
        "addresses": addresses,
        "total_items": total_items,
        "total_price": total_price,
        "total_discount": total_discount,   # ✅ use same variable name as cart.html
        "order_total": order_total,
    })

@login_required
def edit_address(request, id):
    address = Address.objects.get(id=id, user=request.user)

    if request.method == 'POST':
        address.name = request.POST.get('name')    
        address.phone = request.POST.get('phone') 
        address.house = request.POST.get('house')
        address.area = request.POST.get('area')
        address.pincode = request.POST.get('pincode')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.save()
        return redirect('address_list')

    return render(request, 'edit_address.html', {
        'address': address
    })

# users/views.py (or wherever your payment view is)

from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from product.models import Product
from users.models import Address  # change if app name different

def payment(request):
    # ✅ POST 1: coming from Address page
    if request.method == "POST" and request.POST.get("address_id"):
        address_id = request.POST.get("address_id")
        address = get_object_or_404(Address, id=address_id, user=request.user)
        request.session["selected_address_id"] = address.id
        return redirect("payment")

    # ✅ POST 2: coming from Continue button on Payment page
    if request.method == "POST" and request.POST.get("payment_method"):
        method = request.POST.get("payment_method")      # cod / online
        resell = request.POST.get("is_reselling", "0")   # 0 / 1

        request.session["payment_method"] = method
        request.session["is_reselling"] = resell

        # ✅ after payment selection go to orders/summary page
        return redirect("orders")  # change to any url name that exists

    # ===== GET: render payment page =====
    cart = request.session.get("cart", {})

    total_items = 0
    total_price = 0 

    for key, item in cart.items():
        product = get_object_or_404(Product, id=item["product_id"])
        qty = int(item.get("qty", 1))
        total_items += qty
        total_price += Decimal(str(product.price)) * qty

    total_discount = Decimal("0.00")
    order_total = total_price - total_discount

    save_amount = Decimal("28.00") if order_total >= 28 else Decimal("0.00")
    online_price = order_total - save_amount

    selected_address = None
    selected_id = request.session.get("selected_address_id")
    if selected_id:
        selected_address = Address.objects.filter(id=selected_id, user=request.user).first()

    return render(request, "payment.html", {
        "total_items": total_items,
        "total_price": total_price,
        "total_discount": total_discount,
        "order_total": order_total,
        "online_price": online_price,
        "save_amount": save_amount,
        "selected_address": selected_address,
    })

def summary(request):
    return render(request, "summary.html")

def cart_page(request):
    return render(request, "cart.html", {"active_step": 1})

def address_page(request):
    return render(request, "address.html", {"active_step": 2})

def payment_page(request):
    return render(request, "payment.html", {"active_step": 3})

def summary_page(request):
    return render(request, "summary.html", {"active_step": 4})

from django.shortcuts import get_object_or_404

@login_required
def enter_address(request):
    if request.method == "POST":
        a = Address.objects.create(
            user=request.user,
            name=request.POST.get("name","").strip(),
            phone=request.POST.get("phone","").strip(),
            house=request.POST.get("house","").strip(),
            area=request.POST.get("area","").strip(),
            city=request.POST.get("city","").strip(),
            state=request.POST.get("state","").strip(),
            pincode=request.POST.get("pincode","").strip(),
        )

        # ✅ Meesho logic: remember selected address
        request.session["selected_address_id"] = a.id

        # ✅ Back to Review Checkout page
        return redirect("review_checkout")   # change if your url name is different

    return redirect("review_checkout")


@login_required
def select_address(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)
    request.session["selected_address_id"] = address.id
    return redirect("review_checkout")

def orders(request):
    return render(request, "my_orders.html") 