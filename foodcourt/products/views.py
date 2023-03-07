# Create your views here.

from django_filters import rest_framework as django_filters
from rest_framework import generics, filters

from .models import Product
from .serializer import ProductListSerializer, ProductDetailSerializer


# product list
class ProductFilter(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
        }

class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    queryset = Product.objects.all()
    filter_backends = [filters.OrderingFilter, filters.SearchFilter, django_filters.DjangoFilterBackend]
    search_fields = ['name', 'description','price']
    ordering_fields = ['price']
    filterset_class = ProductFilter


# product detail

class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer