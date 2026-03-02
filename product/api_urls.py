from django.urls import path
from .api_views import product_api

urlpatterns = [
    path('', product_api, name='product_api'),  # API endpoint
]
