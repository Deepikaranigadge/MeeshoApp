from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('admin/', admin.site.urls),

    # Home app
    path('', include('home.urls')),
    path('', include('users.urls')),   # home loads here
    # Users app
    path('users/', include('users.urls')),

    # Product app - normal pages (listing & detail)
    path('products/', include('product.urls')),

    # Product API
    path('api/products/', include('product.api_urls')),

    # Cart
    path('cart/', include('cart.urls')),


    # Orders
    path('orders/', include('orders.urls')),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path("", include("product.urls")),
    path("orders/", include("orders.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
