from rest_framework import serializers
from products.models import Product, Category, Brand, UnitOfMeasure, Rating


# product list

class ProductListSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('image','name', 'price', 'rating')

    def get_rating(self, obj):
        # Calculate the average rating for the product
        ratings = Rating.objects.filter(product=obj)
        if ratings.exists():
            rating_sum = sum(rating.score for rating in ratings)
            return rating_sum / ratings.count()
        else:
            return 0

# product detail
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'

class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = '__all__'

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    brand = BrandSerializer()
    unit_of_measure = UnitOfMeasureSerializer()

    class Meta:
        model = Product
        fields = '__all__'
        depth = 2

#