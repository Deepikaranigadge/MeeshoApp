from django.urls import path
from . import views, api_views
from django.contrib.auth.views import LogoutView
from home import views as home_views 
from cart import views as cart_views

urlpatterns = [
    path('', home_views.home, name='home'),  
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("profile/", views.profile, name="profile"),
    path("orders/", views.orders, name="orders"),
    path("logout/", LogoutView.as_view(next_page="/"), name="logout"),
    path("logout/", views.logout_view, name="logout"),
     # API (OTP + JWT)
    path('signup/', views.signup, name='signup'),
    path('otp/', views.otp_page, name='otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
     # ADDRESS
    #path('address/', views.address_list, name='address_list'),
    path('address/add/', views.add_address, name='add_address'),
    path('address/edit/<int:id>/', views.edit_address, name='edit_address'),
    path("payment/", views.payment, name="payment"),
    path("summary/", views.summary, name="summary"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path("address/", cart_views.address_list, name="address_list"),
    path("address/enter/", views.enter_address, name="enter_address"), # NEW Meesho flow
    path("address/select/<int:id>/", views.select_address, name="select_address"),
    path("orders/", views.orders, name="orders"), 
]

