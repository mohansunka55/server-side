from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent_category = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories')

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    calories = models.IntegerField(blank=True, null=True)
    fat = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    carbohydrates = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    protein = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    sodium = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    def __str__(self):
        return self.name


class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField(choices=((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')))
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('product', 'user'),)