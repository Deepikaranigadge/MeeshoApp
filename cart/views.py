from decimal import Decimal
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse

from product.models import Product, ResellerMargin
from .models import Cart, CartItem
from users.models import Address


@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    items = CartItem.objects.select_related("product").filter(user=request.user)

    total_items = 0
    total_price = Decimal("0.00")      # MRP total
    total_discount = Decimal("0.00")   # discount total
    order_total = Decimal("0.00")      # selling total

    for item in items:
        qty = int(item.qty)
        price = Decimal(str(item.product.price or 0))
        mrp = Decimal(str(getattr(item.product, "mrp", 0) or 0))

        total_items += qty
        total_price += mrp * qty
        order_total += price * qty

        if mrp > price:
            total_discount += (mrp - price) * qty

    return render(request, "address.html", {
        "addresses": addresses,
        "total_items": total_items,
        "total_price": total_price,
        "total_discount": total_discount,
        "order_total": order_total,
    })


@login_required(login_url='login')
def add_to_cart(request, product_id):
    if request.method != "POST":
        return redirect("product_detail", id=product_id)

    product = get_object_or_404(Product, id=product_id)
    size = request.POST.get("size")

    if not size:
        messages.error(request, "Please select a size")
        return redirect("product_detail", id=product_id)

    item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        size=size,
        defaults={"qty": 1}
    )

    if not created:
        item.qty += 1
        item.save()

    messages.success(request, "Added to cart")
    return redirect("product_detail", id=product_id)


def cart_page(request):
    if not request.user.is_authenticated:
        return redirect("login")

    cart_items = CartItem.objects.select_related("product").filter(user=request.user)

    # ✅ If cart is empty → show empty_cart.html (Meesho empty UI)
    if not cart_items.exists():
        return render(request, "empty_cart.html")
    
    total_items = 0
    total_price = Decimal("0.00")
    total_discount = Decimal("0.00")
    order_total = Decimal("0.00")

    for item in cart_items:
        qty = int(item.qty)

        price = Decimal(str(item.product.price or 0))
        mrp = Decimal(str(getattr(item.product, "mrp", 0) or 0))

        total_items += qty
        total_price += mrp * qty
        order_total += price * qty

        if mrp > price:
            total_discount += (mrp - price) * qty

    return render(request, "cart.html", {
        "cart_items": cart_items,
        "total_items": total_items,
        "total_price": total_price,
        "total_discount": total_discount,
        "order_total": order_total,
    })


@login_required
def remove_from_cart(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(CartItem, id=item_id, user=request.user)
        item.delete()
    return redirect("cart_page")


def buy_now(request, id):
    if request.method != "POST":
        return redirect("product_detail", id=id)

    size = request.POST.get("size")
    if not size:
        messages.error(request, "Please select a size")
        return redirect("product_detail", id=id)

    product = get_object_or_404(Product, id=id)

    CartItem.objects.filter(user=request.user).delete()

    CartItem.objects.create(
        user=request.user,
        product=product,
        size=size,
        qty=1
    )

    return redirect("address_list")


def update_cart_item(request, item_id):
    if request.method != "POST" or not request.user.is_authenticated:
        return redirect("cart_page")

    item = get_object_or_404(CartItem, id=item_id, user=request.user)

    size = request.POST.get("size", "").strip()
    qty = int(request.POST.get("qty", item.qty))

    if not size:
        messages.error(request, "Please select a size")
        return redirect("cart_page")

    if qty < 1:
        qty = 1
    if qty > 10:
        qty = 10

    existing = CartItem.objects.filter(
        user=request.user,
        product=item.product,
        size=size
    ).exclude(id=item.id).first()

    if existing:
        existing.qty += qty
        existing.save()
        item.delete()
    else:
        item.size = size
        item.qty = qty
        item.save()

    messages.success(request, "Cart updated")

    # ✅ This part is already added correctly
    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)

    return redirect("cart_page")

@login_required
def payment(request):
    if request.method == "POST":
        address_id = request.POST.get("address_id")
        if address_id:
            request.session["selected_address_id"] = int(address_id)

    items = CartItem.objects.select_related("product").filter(user=request.user)

    total_items = 0
    total_price = Decimal("0.00")
    total_discount = Decimal("0.00")
    order_total = Decimal("0.00")

    for item in items:
        qty = int(item.qty)

        price = Decimal(str(item.product.price or 0))
        mrp = Decimal(str(getattr(item.product, "mrp", 0) or 0))

        total_items += qty
        total_price += mrp * qty
        order_total += price * qty

        if mrp > price:
            total_discount += (mrp - price) * qty

    return render(request, "payment.html", {
        "total_items": total_items,
        "total_price": total_price,
        "total_discount": total_discount,
        "order_total": order_total,
    })


@login_required
def summary(request):
    items = CartItem.objects.select_related("product").filter(user=request.user)

    cart_items = []
    total_items = 0
    total_price = Decimal("0.00")
    total_discount = Decimal("0.00")
    order_total = Decimal("0.00")

    for item in items:
        qty = int(item.qty)

        price = Decimal(str(item.product.price or 0))
        mrp = Decimal(str(getattr(item.product, "mrp", 0) or 0))

        total_items += qty
        total_price += mrp * qty
        order_total += price * qty

        if mrp > price:
            total_discount += (mrp - price) * qty

        cart_items.append({
            "item_id": item.id,
            "product": item.product,
            "size": item.size,
            "qty": qty,
            "line_total": price * qty
        })

    address_id = request.session.get("selected_address_id")
    address = None
    if address_id:
        address = Address.objects.filter(id=address_id, user=request.user).first()

    est_date = timezone.localdate() + timedelta(days=7)
    estimated_delivery = est_date.strftime("%A, %d %b")

    return render(request, "summary.html", {
        "cart_items": cart_items,
        "total_items": total_items,
        "total_price": total_price,
        "total_discount": total_discount,
        "order_total": order_total,
        "address": address,
        "estimated_delivery": estimated_delivery,
    })


# ✅ PLACE ORDER -> redirects to confirmed page
@login_required
@require_POST
def place_order(request):
    # ✅ keep selected address id for success page (same style you used)
    request.session["success_address_id"] = request.session.get("selected_address_id")

    # ✅ go to confirmed page
    return redirect("order_confirmed")


# ✅ CONFIRMED PAGE -> after 3s goes to success page
@login_required
def order_confirmed(request):
    # success page url
    success_url = reverse("order_success")
    return render(request, "order_confirmed.html", {
        "redirect_url": success_url
    })


# ✅ SUCCESS PAGE
@login_required
def order_success(request):
    items = CartItem.objects.select_related("product").filter(user=request.user)

    total_price = Decimal("0.00")
    total_items = 0

    for it in items:
        total_items += int(it.qty)
        total_price += Decimal(str(it.product.price)) * Decimal(it.qty)

    address_id = request.session.get("success_address_id") or request.session.get("selected_address_id")
    address = Address.objects.filter(id=address_id, user=request.user).first() if address_id else None

    context = {
        "order_id": request.session.get("last_order_id", "254238652052744512"),
        "items": items,
        "total_items": total_items,
        "total_price": total_price,
        "order_total": total_price,
        "estimated_delivery": "Sunday, 22nd Feb",
        "address": address,
    }

    return render(request, "order_success.html", context)


# ✅ BUY NOW REVIEW (unchanged)
def buy_now_review(request, product_id):
    p = get_object_or_404(Product, id=product_id)

    qty = 1
    size = request.POST.get("size") or "Free Size"

    mrp = getattr(p, "mrp", None) or 0
    price = int(p.price)
    mrp = int(mrp) if mrp else 0

    discount = max(mrp - price, 0) if mrp else 0
    total = price

    context = {
        "eta_text": "Wednesday, 25th Feb",
        "item": {
            "title": p.title,
            "image": p.image.url,
            "price": price,
            "mrp": mrp if mrp else "",
            "off_text": "6% Off" if mrp else "",
            "size": size,
            "qty": qty,
            "seller": "GOVINDJI ART",
        },
        "items_count": 1,
        "price_details": {
            "product_price": mrp if mrp else price,
            "discount": discount,
            "total": total,
        },
        "address": {
            "name": request.user.get_full_name() or "Deepikarani",
            "line1": "#294, Shri Makkala Maramma Devi Temple",
            "line2": "Muneshwar Block, Bengaluru",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560003",
            "phone": "",
        }
    }
    return render(request, "review_checkout.html", context)

@login_required
def empty_cart(request):
    return render(request, "empty_cart.html")


from users.models import Address

@login_required
def summary_page(request):
    addresses = Address.objects.filter(user=request.user).order_by("-id")

    selected_id = request.session.get("selected_address_id")

    selected_address = None
    if selected_id:
        selected_address = addresses.filter(id=selected_id).first()

    if not selected_address and addresses.exists():
        selected_address = addresses.first()
        request.session["selected_address_id"] = selected_address.id

    context = {
        "addresses": addresses,
        "selected_address": selected_address,
        "address": selected_address,  # ✅ so your template works
    }
    return render(request, "summary.html", context)


@login_required
def set_delivery_address(request):
    if request.method == "POST":
        addr_id = request.POST.get("address_id")
        if addr_id:
            addr = get_object_or_404(Address, id=addr_id, user=request.user)
            request.session["selected_address_id"] = addr.id
    return redirect("summary")