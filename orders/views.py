from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
import time, random

from cart.models import Cart, CartItem
from product.models import Product
from .models import Order, OrderItem
from users.models import Address

from datetime import timedelta
from django.utils import timezone


@login_required
def order_list(request):
    return render(request, "orders/orders.html")


@login_required
@transaction.atomic
def place_order(request):
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect("cart_page")

    product_ids = [ci.product_id for ci in cart_items]
    products = Product.objects.select_for_update().filter(id__in=product_ids)
    product_map = {p.id: p for p in products}

    total_amount = 0
    order = Order.objects.create(user=request.user, status="placed", total_amount=0)

    for ci in cart_items:
        p = product_map[ci.product_id]

        if ci.qty > p.stock:
            messages.error(request, f"Not enough stock for {p.title}. Available: {p.stock}")
            return redirect("cart_page")

        OrderItem.objects.create(
            order=order,
            product=p,
            quantity=ci.qty,
            price=p.price
        )

        # ✅ STOCK UPDATE
        p.stock -= ci.qty
        p.save(update_fields=["stock"])

        total_amount += ci.qty * p.price

    order.total_amount = total_amount
    order.save(update_fields=["total_amount"])

    # ✅ SAVE DATA FOR order_success.html (MATCH YOUR TEMPLATE VARIABLES)
    # items for product loop (so it still shows after cart is deleted)
    request.session["last_items"] = [
        {
            "product": {
                "title": product_map[ci.product_id].title,
                "price": float(product_map[ci.product_id].price),
                "image_url": (product_map[ci.product_id].image.url if product_map[ci.product_id].image else ""),
                "seller_name": getattr(product_map[ci.product_id], "seller_name", ""),
            },
            "size": ci.size,
            "qty": int(ci.qty),
        }
        for ci in cart_items
    ]

    # total items
    request.session["last_total_items"] = sum(int(ci.qty) for ci in cart_items)

    # total product price (MRP total) - fallback to price if mrp not available
    mrp_total = 0
    for ci in cart_items:
        p = product_map[ci.product_id]
        mrp = getattr(p, "mrp", None) or p.price
        mrp_total += int(mrp) * int(ci.qty)

    request.session["last_total_price"] = float(mrp_total)        # ✅ Total Product Price
    request.session["last_order_total"] = float(total_amount)     # ✅ Order Total

    # ✅ remove ordered items from cart
    cart_items.delete()

    # ✅ Meesho-style long numeric Order ID (18 digits)
    base = str(int(time.time() * 1000))          # 13 digits (milliseconds)
    extra = str(random.randint(10000, 99999))    # 5 digits
    order_id = (base + extra)[:18]

    # ✅ go to confirmed page (then auto to success)
    return redirect(reverse("order_confirmed") + f"?oid={order_id}")


# ✅ BUY NOW FLOW (UNCHANGED)
@login_required
def buy_now_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        size = request.POST.get("size")
        if not size:
            return redirect("product_detail", product_id=product.id)

        request.session["buy_now"] = {
            "product_id": product.id,
            "size": size,
            "qty": 1
        }
        return redirect("review_checkout")

    return redirect("product_detail", product_id=product.id)


@login_required
def review_checkout(request):
    data = request.session.get("buy_now")
    if not data:
        return redirect("home")

    product = get_object_or_404(Product, id=data["product_id"])

    qty = int(data.get("qty", 1))
    mrp = int(product.mrp or 0)
    price = int(product.price or 0)
    discount_amount = (mrp - price) if mrp > price else 0

    addresses = Address.objects.filter(user=request.user).order_by("-id")

    addresses_ui = []
    for a in addresses:
        name = (
            getattr(a, "full_name", None)
            or getattr(a, "name", None)
            or getattr(a, "username", None)
            or getattr(a, "receiver_name", None)
            or str(getattr(a, "user", ""))
        )

        phone = (
            getattr(a, "phone", None)
            or getattr(a, "phone_number", None)
            or getattr(a, "mobile", None)
            or getattr(a, "contact", None)
            or ""
        )

        parts = []
        for field in ["house", "flat", "building", "address", "address_line1", "line1", "street"]:
            v = getattr(a, field, None)
            if v:
                parts.append(str(v))
                break

        for field in ["area", "locality", "landmark", "address_line2", "line2"]:
            v = getattr(a, field, None)
            if v:
                parts.append(str(v))

        for field in ["city", "district", "town"]:
            v = getattr(a, field, None)
            if v:
                parts.append(str(v))
                break

        for field in ["state", "province"]:
            v = getattr(a, field, None)
            if v:
                parts.append(str(v))
                break

        pin = getattr(a, "pincode", None) or getattr(a, "pin", None) or getattr(a, "zip_code", None) or ""

        line = ", ".join([p for p in parts if p])
        if pin:
            line = f"{line} - {pin}" if line else str(pin)

        addresses_ui.append({
            "id": a.id,
            "name": name,
            "phone": phone,
            "line": line,
        })

    return render(request, "orders/review_checkout.html", {
        "product": product,
        "size": data["size"],
        "qty": qty,
        "active_step": 1,
        "discount_amount": discount_amount,
        "addresses_ui": addresses_ui,
    })


# ✅ CONFIRMED PAGE
@login_required
def order_confirmed(request):
    order_id = request.GET.get("oid")
    success_url = reverse("order_success") + f"?oid={order_id}"
    return render(request, "order_confirmed.html", {
        "redirect_url": success_url
    })


# ✅ SUCCESS PAGE
@login_required
def order_success(request):
    order_id = request.GET.get("oid")
    eta_text = "3 - 5 days"

    address_id = request.session.get("selected_address_id")
    address = Address.objects.filter(id=address_id, user=request.user).first() if address_id else None

    # ✅ Estimated Delivery (same as summary page)
    est_date = timezone.localdate() + timedelta(days=7)
    estimated_delivery = est_date.strftime("%A, %d %b")

    # ✅ Build "items" objects matching your template usage: item.product.title, item.product.price, item.product.image.url
    raw_items = request.session.get("last_items", [])
    items = []
    for it in raw_items:
        class Obj: pass
        item_obj = Obj()
        item_obj.size = it.get("size")
        item_obj.qty = it.get("qty")

        product_obj = Obj()
        product_obj.title = it["product"].get("title")
        product_obj.price = it["product"].get("price")
        product_obj.seller_name = it["product"].get("seller_name")

        # fake image object with .url
        img_url = it["product"].get("image_url", "")
        if img_url:
            img = Obj()
            img.url = img_url
            product_obj.image = img
        else:
            product_obj.image = None

        item_obj.product = product_obj
        items.append(item_obj)

    context = {
        "order_id": order_id,
        "eta_text": eta_text,
        "estimated_delivery": estimated_delivery,
        "item_count": request.GET.get("items", 1),
        "total_paid": request.GET.get("total", 0),
        "payment_mode": request.GET.get("pay", "COD / Online"),
        "address": address,

        # ✅ THESE MATCH YOUR order_success.html
        "items": items,
        "total_items": request.session.get("last_total_items", 0),
        "total_price": request.session.get("last_total_price", 0),
        "order_total": request.session.get("last_order_total", 0),

         "total_discount": max(float(request.session.get("last_total_price", 0)) - float(request.session.get("last_order_total", 0)), 0),
    }
    return render(request, "order_success.html", context)

def my_orders(request):
    return render(request, "my_orders.html")


# orders/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from product.models import Product  # adjust import if your app name differs


@login_required
def buy_payment(request):
    # 1) Get product_id from URL (?product_id=10) or from session fallback
    product_id = request.GET.get("product_id") or request.session.get("checkout_product_id")
    if not product_id:
        return redirect("home")  # or redirect("cart_page") / review page

    product = get_object_or_404(Product, id=product_id)

    # 2) qty / size (from url or session fallback)
    qty = request.GET.get("qty") or request.session.get("checkout_qty") or 1
    try:
        qty = int(qty)
    except:
        qty = 1
    if qty < 1:
        qty = 1

    size = request.GET.get("size") or request.session.get("checkout_size") or ""

    # 3) Calculate totals
    # If mrp is 0/None, use price as mrp
    mrp = product.mrp if product.mrp and product.mrp > 0 else product.price

    product_price_total = Decimal(mrp) * qty          # MRP * qty
    selling_total = Decimal(product.price) * qty      # Selling price * qty
    discount_amount = product_price_total - selling_total
    if discount_amount < 0:
        discount_amount = Decimal("0")

    order_total = selling_total

    context = {
        "product": product,
        "qty": qty,
        "size": size,
        "product_price_total": product_price_total,
        "discount_amount": discount_amount,
        "order_total": order_total,
    }
    return render(request, "orders/buy_payment.html", context)