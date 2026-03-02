from django.urls import path
from . import views
from .views import place_order
from .views import my_orders, buy_payment

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path("place-order/", place_order, name="place_order"),
    path("buy-now/<int:product_id>/", views.buy_now_review, name="buy_now_review"),
    path("review-checkout/", views.review_checkout, name="review_checkout"),
    path("confirmed/", views.order_confirmed, name="order_confirmed"),
    path("success/", views.order_success, name="order_success"),
    path("my-orders/", my_orders, name="orders"),
    path("buy-payment/", buy_payment, name="buy_payment"),

    
]
