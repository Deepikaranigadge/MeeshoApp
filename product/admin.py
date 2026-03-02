from django.contrib import admin
from .models import Product, Size, ProductImage, ProductHighlight, ProductPincode
from .models import PincodeLocation

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 4   # shows 4 image upload boxes like Meesho


class ProductHighlightInline(admin.TabularInline):
    model = ProductHighlight
    extra = 3
    fields = ("group", "label", "value", "order")
    ordering = ("group", "order", "label")


# ✅ Pincode Inline (Optional: show pincode rules inside product page)
class ProductPincodeInline(admin.TabularInline):
    model = ProductPincode
    extra = 2
    fields = ("pincode", "area_name","is_serviceable", "delivery_days", "dispatch_days")
    autocomplete_fields = ("product",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "price", "mrp", "stock", "delivery_check_enabled")
    list_filter = ("category", "delivery_check_enabled")
    search_fields = ("title", "category")
    filter_horizontal = ("sizes",)

    # ✅ All related items in one place like Meesho admin
    inlines = [
        ProductImageInline,
        ProductHighlightInline,
        ProductPincodeInline,   # 👈 add pincode enable/disable here
    ]

    list_editable = ("delivery_check_enabled",)


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    pass


@admin.register(ProductHighlight)
class ProductHighlightAdmin(admin.ModelAdmin):
    list_display = ("product", "group", "label", "value", "order")
    list_filter = ("group",)
    search_fields = ("product__title", "label", "value")


# ✅ Separate Admin Page for ProductPincode (optional)
@admin.register(ProductPincode)
class ProductPincodeAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "pincode", "is_serviceable", "delivery_days", "dispatch_days")
    list_editable = ("is_serviceable", "delivery_days", "dispatch_days")
    list_filter = ("is_serviceable",)
    search_fields = ("pincode", "product__title")

@admin.register(PincodeLocation)
class PincodeLocationAdmin(admin.ModelAdmin):
    list_display = ("pincode", "area_name")
    search_fields = ("pincode", "area_name")
