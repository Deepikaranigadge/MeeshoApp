def cart_count(request):
    cart = request.session.get("cart", {})
    total_qty = sum(item.get("qty", 0) for item in cart.values())
    return {"cart_count": total_qty}

