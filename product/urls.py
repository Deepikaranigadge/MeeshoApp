from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='product_index'),

    # ✅ Product detail (ONLY ONE)
    path('product/<int:id>/', views.product_detail, name='product_detail'),

    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path("buy-now/<int:id>/", views.buy_now, name="buy_now"),

    path("saree/", views.saree_products, name="saree_products"),
    path("kurti/", views.kurti_products, name="kurti_products"),
    path("search/", views.search_products, name="search_products"),
    path("product/<int:product_id>/check-delivery/", views.check_delivery, name="check_delivery"),
    path("category/<slug:slug>/", views.category_products, name="category_products"),

]