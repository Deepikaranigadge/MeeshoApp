from django.db import models
from users.models import User

from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)   # Ethnic Wear -> ethnic-wear
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=10)
    def __str__(self):
        return self.name
    
from django.db import models
from decimal import Decimal, ROUND_HALF_UP

# keep your Size model import if it's in another file
# from .models import Size   (NOT needed if Size is in same file)

class Product(models.Model):
    # ✅ Seller name (like Fabflee, Anouk, etc.)
    seller_name = models.CharField(max_length=100, default="Meesho Seller")
    category = models.CharField(max_length=100, default="cloths")
    title = models.CharField(max_length=255)

    image = models.ImageField(upload_to="products/")

    # ✅ Meesho style pricing
    mrp = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,default=0)

    # ✅ Optional: set discount per product (admin) -> price auto calculated
    discount_percent = models.PositiveIntegerField(blank=True, null=True, default=0, help_text="0 to 100")

    # old fixed highlight fields (optional)
    color = models.CharField(max_length=50, blank=True, null=True)
    fabric = models.CharField(max_length=50, blank=True, null=True)
    fit = models.CharField(max_length=50, blank=True, null=True)
    length = models.CharField(max_length=50, blank=True, null=True)

    # optional but needed if you want these filters
    gender = models.CharField(max_length=20, blank=True, null=True)  # Men/Women/Boys/Girls
    dial_shape = models.CharField(max_length=20, blank=True, null=True)
    combo_of = models.PositiveIntegerField(default=1)

    sizes = models.ManyToManyField("Size", blank=True)
    stock = models.PositiveIntegerField(default=0)

     # ✅ ADD THESE FOR MEESHO-LIKE BREADCRUMB
    main_category  = models.CharField(max_length=120, blank=True, null=True)   # Men / Women
    sub_category   = models.CharField(max_length=120, blank=True, null=True)   # Men Western Top Wear
    child_category = models.CharField(max_length=120, blank=True, null=True)   # Gym Vests

    # ✅ Master switch (optional)
    delivery_check_enabled = models.BooleanField(default=True)

    # ✅ Highlights JSON
    product_highlights = models.JSONField(default=dict, blank=True)

    # ✅ Additional Details JSON
    additional_details = models.JSONField(default=dict, blank=True)

    # similar products
    similar_products = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="similar_to"
    )

    def save(self, *args, **kwargs):
        # ✅ If admin sets discount_percent, auto-calc price using mrp
        if self.mrp and self.discount_percent:
            mrp = Decimal(self.mrp)
            pct = Decimal(self.discount_percent) / Decimal(100)
            new_price = mrp * (Decimal(1) - pct)
            self.price = new_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        super().save(*args, **kwargs)

    @property
    def calc_discount_percent(self):
        # ✅ If you don't want to store discount, this calculates from mrp & price
        if self.mrp and self.price and self.mrp > 0 and self.mrp > self.price:
            off = (Decimal(self.mrp) - Decimal(self.price)) / Decimal(self.mrp) * Decimal(100)
            return int(off.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return 0

    def __str__(self):
        return self.title

class ProductPincode(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="pincode_rules")
    pincode = models.CharField(max_length=6)

    area_name = models.CharField(max_length=100, blank=True, null=True)  # ✅ NEW

    # ✅ enable / disable delivery for THIS product + THIS pincode
    is_serviceable = models.BooleanField(default=True)

    # Optional fields (to show delivery date + dispatch days)
    delivery_days = models.PositiveIntegerField(default=3)   # today + 3 days
    dispatch_days = models.PositiveIntegerField(default=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "pincode")  # no duplicate rows
        indexes = [models.Index(fields=["product", "pincode"])]

    def __str__(self):
        return f"{self.product.title} - {self.pincode} - {self.area_name}"

  #pin code location  
class PincodeLocation(models.Model):
    pincode = models.CharField(max_length=6, unique=True)
    area_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.pincode} - {self.area_name}"

class ProductHighlight(models.Model):
    GROUP_CHOICES = (
        ("Product Highlights", "Product Highlights"),
        ("Additional Details", "Additional Details"),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="highlights")
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    group = models.CharField(max_length=50, choices=GROUP_CHOICES, default="Product Highlights")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["group", "order", "label"]

    def __str__(self):
        return f"{self.product.title} - {self.label}: {self.value}"
    
class ResellerMargin(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    margin_percent = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.title} - {self.margin_percent}%"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product.title} - {self.rating}"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="gallery", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/gallery/")

    def __str__(self):
        return f"{self.product.title} - gallery image"
