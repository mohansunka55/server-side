import string, random
from django.utils.text import slugify
from enum import Enum
from rest_framework.permissions import BasePermission

from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def get_user_access_type(user):
    type = "customer_care"
    if user.is_customer_care:
        type = "customer_care"

    if user.is_collection_agent:
        type = "collection_agent"

    if user.is_agent:
        type = "agent"

    if user.is_cashier:
        type = "cashier"

    if user.is_finance:
        type = "finance"

    if user.is_staff:
        type = "staff"

    if user.is_admin:
        type = "admin"

    return {
        'type': type,
    }


class IsEngineerAuthenticated(BasePermission):
    def has_permission(self, request, view):
        print(request.user)
        return bool(request.user.is_engineer and request.user.is_authenticated)


class GenderEnumTypes(Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHERS = "OTHERS"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]