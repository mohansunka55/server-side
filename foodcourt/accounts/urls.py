from django.urls import path,include

urlpatterns = [
    path('api/v1/admin/', include("accounts.api_v1_admin.urls")),
]