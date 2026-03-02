from django.urls import path
from . import views
from .views import buy_now_review
urlpatterns = [
    path("add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("", views.cart_page, name="cart_page"),
    path("remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("buy/<int:id>/", views.buy_now, name="buy_now"),
    path("update/<int:item_id>/", views.update_cart_item, name="update_cart_item"),
    path("payment/", views.payment, name="payment"),
    path("summary/", views.summary, name="summary"),
    path("place-order/", views.place_order, name="place_order"),
    path("order-success/", views.order_success, name="order_success"),
    path("checkout/review/<int:product_id>/", buy_now_review, name="buy_now_review"),
    path("empty/", views.empty_cart, name="empty_cart"),
    path("summary/", views.summary_page, name="summary"),
    path("set-address/", views.set_delivery_address, name="set_delivery_address"),
]
