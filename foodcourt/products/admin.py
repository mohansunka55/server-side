from django.contrib import admin

from products.models import *

# Register your models here.
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Brand)
admin.site.register(UnitOfMeasure)
admin.site.register(Rating)