from django.shortcuts import render
from django.db.models import Q
from product.models import Product

def home(request):
    qs = Product.objects.all()   # 👈 1) START queryset

    # ✅ 2) ADD PRICE FILTER HERE (PASTE YOUR CODE HERE)
    price_range = request.GET.get("price_range")
    if price_range:
        if price_range.endswith("+"):
            min_price = int(price_range.replace("+", ""))
            qs = qs.filter(price__gte=min_price)
        else:
            min_price, max_price = price_range.split("-")
            qs = qs.filter(price__gte=int(min_price), price__lte=int(max_price))

    # ✅ Color (case-insensitive + trims spaces)
    colors = [c.strip() for c in request.GET.getlist("color") if c.strip()]
    if colors:
        qc = Q()
        for c in colors:
            qc |= Q(color__iexact=c)
        qs = qs.filter(qc)

    # ✅ Fabric (case-insensitive)
    fabrics = [f.strip() for f in request.GET.getlist("fabric") if f.strip()]
    if fabrics:
        qf = Q()
        for f in fabrics:
            qf |= Q(fabric__iexact=f)
        qs = qs.filter(qf)

  # ✅ 👉 ADD COMBO FILTER HERE
    combos = request.GET.getlist("combo_of")
    if combos:
        if "4+" in combos:
            combos = [c for c in combos if c != "4+"]
            qs = qs.filter(combo_of__gte=4)
            if combos:
                qs = qs | Product.objects.filter(combo_of__in=combos)
        else:
            qs = qs.filter(combo_of__in=combos)
            
    # ✅ Gender (case-insensitive)
    genders = [g.strip() for g in request.GET.getlist("gender") if g.strip()]
    if genders:
        qg = Q()
        for g in genders:
            qg |= Q(gender__iexact=g)
        qs = qs.filter(qg)

    # ✅ Dial shape (case-insensitive)
    dial_shapes = [d.strip() for d in request.GET.getlist("dial_shape") if d.strip()]
    if dial_shapes:
        qd = Q()
        for d in dial_shapes:
            qd |= Q(dial_shape__iexact=d)
        qs = qs.filter(qd)

    # ✅ Size M2M (case-insensitive)
    sizes = [s.strip() for s in request.GET.getlist("size") if s.strip()]
    if sizes:
        qs = qs.filter(sizes__name__in=sizes).distinct()

    # ✅ SORT
    sort = request.GET.get("sort", "relevance")
    if sort == "price_low":
        qs = qs.order_by("price")
    elif sort == "price_high":
        qs = qs.order_by("-price")

    context = {
        "products": qs,
        "sel_colors": colors,
        "sel_fabrics": fabrics,
        "sel_genders": genders,
        "sel_dial_shapes": dial_shapes,
        "sel_sizes": sizes,
    }
    return render(request, "index.html", context)

def contact(request):
    return render(request, "contact.html")
