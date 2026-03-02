from django.shortcuts import render, get_object_or_404
from product.models import Product, Size

# Home / product listing
def index(request):
    products = Product.objects.all()
    return render(request, 'index.html', {'products': products})

# Product detail page
from django.shortcuts import render, get_object_or_404
from .models import Product

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)

    # ✅ 1) PRODUCT HIGHLIGHTS (from normal fields + JSONField)
    product_highlights = []

    if product.color:
        product_highlights.append({"label": "Color", "value": product.color})

    if product.fabric:
        product_highlights.append({"label": "Fabric", "value": product.fabric})

    if product.fit:
        product_highlights.append({"label": "Fit / Shape", "value": product.fit})

    if product.length:
        product_highlights.append({"label": "Length", "value": product.length})

    if product.product_highlights:
        for k, v in product.product_highlights.items():
            if v not in ("", None):
                product_highlights.append({"label": str(k), "value": str(v)})

    # ✅ 2) ADDITIONAL DETAILS (from JSONField)
    additional_details = []
    if product.additional_details:
        for k, v in product.additional_details.items():
            if v not in ("", None):
                additional_details.append({"label": str(k), "value": str(v)})

    # ✅ 3) SIMILAR PRODUCTS
    similar_products = []
    if hasattr(product, "similar_products"):
        similar_products = product.similar_products.all()

 # ✅ 4) BREADCRUMBS (EXACT Meesho 5 steps using new fields)
    breadcrumbs = [
       {"name": "Home", "url": "/"},
       {"name": product.main_category or "Category", "url": "#"},
       {"name": product.sub_category or "Sub Category", "url": "#"},
       {"name": product.child_category or "Child Category", "url": "#"},
       {"name": product.title[:18] + ("..." if len(product.title) > 18 else ""), "url": None},
]
    return render(request, "product_detail.html", {
        "product": product,
        "product_highlights": product_highlights,
        "additional_details": additional_details,
        "similar_products": similar_products,

        # ✅ ADD THIS
        "breadcrumbs": breadcrumbs,
    })
#categari
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Category, Product

def category_products(request, slug):
    # 1) Get category
    category = get_object_or_404(Category, slug=slug)

    # 2) Start base queryset (only this category products)
    qs = Product.objects.filter(category=category)

    # 3) SORT
    sort = request.GET.get("sort")
    if sort == "price_low":
        qs = qs.order_by("price")
    elif sort == "price_high":
        qs = qs.order_by("-price")
    else:
        qs = qs.order_by("-id")  # default

    # 4) FILTERS (keep only the ones you actually have in Product model)

    # gender (ONLY if Product has gender field)
    gender = request.GET.get("gender")
    if gender:
        qs = qs.filter(gender__iexact=gender)

    # color (ONLY if Product has color field)
    colors = request.GET.getlist("color")
    if colors:
        qs = qs.filter(color__in=colors)

    # fabric (ONLY if Product has fabric field)
    fabrics = request.GET.getlist("fabric")
    if fabrics:
        qs = qs.filter(fabric__in=fabrics)

    # dial_shape (ONLY if Product has dial_shape field)
    dial_shapes = request.GET.getlist("dial_shape")
    if dial_shapes:
        qs = qs.filter(dial_shape__in=dial_shapes)

    # sizes (ONLY if Product has sizes = ManyToManyField(Size))
    sizes = request.GET.getlist("size")
    if sizes:
        qs = qs.filter(sizes__name__in=sizes).distinct()

    # price range
    price_range = request.GET.get("price_range")
    if price_range:
        if price_range.endswith("+"):
            min_price = int(price_range.replace("+", ""))
            qs = qs.filter(price__gte=min_price)
        else:
            mn, mx = price_range.split("-")
            qs = qs.filter(price__gte=int(mn), price__lte=int(mx))

    # 5) Categories list (for sidebar/menu)
    categories = Category.objects.all()

    # 6) Render
    return render(request, "category.html", {
        "category": category,
        "products": qs,
        "categories": categories,
    })


from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from cart.models import CartItem
from .models import Product

def buy_now(request, id):
    if request.method != "POST":
        return redirect("product_detail", id=id)

    product = get_object_or_404(Product, id=id)
    size = request.POST.get("size")

    if not size:
        messages.error(request, "Please select a size")
        return redirect("product_detail", id=id)

    CartItem.objects.create(
        user=request.user,
        product=product,
        size=size,
        qty=1
    )

    # ✅ Redirect to your checkout/address page
    # Change this to your real page name:
    return redirect("address_list")   # OR "checkout" OR "payment"

from django.shortcuts import render
from .models import Product

def saree_products(request):
    products = Product.objects.filter(category__iexact="saree")  # ✅ works with CharField
    return render(request, "products/category_products.html", {
        "products": products,
        "category_name": "Saree"
    })

def kurti_products(request):
    products = Product.objects.filter(category__icontains="kurti")  # CharField case
    return render(request, "products/category_products.html", {
        "products": products,
        "category_name": "Kurti"
    })


from django.shortcuts import render, redirect
from product.models import Product

def search_products(request):
    query = request.GET.get("q", "").strip()

    # ✅ if user typed saree, go to /saree/
    if query.lower() == "saree":
        return redirect("saree_products")   # your saree page url name

    products = Product.objects.none()
    if query:
        products = Product.objects.filter(title__icontains=query) | Product.objects.filter(category__icontains=query)

    return render(request, "products/category_products.html", {
        "products": products,
        "category_name": query.title()
    })

from datetime import timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Product, ProductPincode


@require_POST
def check_delivery(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not product.delivery_check_enabled:
        return JsonResponse({
            "ok": False,
            "message": "Delivery check is disabled for this product."
        })

    pincode = (request.POST.get("pincode") or "").strip()

    if not pincode.isdigit() or len(pincode) != 6:
        return JsonResponse({"ok": False, "message": "Enter a valid 6-digit pincode."})

    rule = ProductPincode.objects.filter(product=product, pincode=pincode).first()

    # ✅ area name comes from ProductPincode now
    area_name = rule.area_name if rule and rule.area_name else pincode

    if not rule or not rule.is_serviceable:
        return JsonResponse({
            "ok": False,
            "message": f"Delivery not available at pincode - {pincode}",
            "area_name": area_name
        })

    delivery_date = timezone.localdate() + timedelta(days=rule.delivery_days)

    return JsonResponse({
        "ok": True,
        "delivery_text": f"Delivery by {delivery_date.strftime('%A, %d %b')}",
        "dispatch_text": f"Dispatch in {rule.dispatch_days} day" + ("s" if rule.dispatch_days != 1 else ""),
        "area_name": area_name
    })
