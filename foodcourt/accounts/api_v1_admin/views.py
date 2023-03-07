import json, django_filters, requests
from django.contrib.auth import get_user_model
from django.forms import DateInput

from django_filters import rest_framework as dj_filter
from rest_framework import status, generics, filters
from rest_framework.authentication import TokenAuthentication, SessionAuthentication, BasicAuthentication

from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from attendance.models import attendanceUserAttendanceInChargeModel

from .serializer import (accountsAdminUserProfileModelSerializer, accountsUserPhonePasswordLoginSerializer,
                         UserCheckAndcreationSerializer, UserLoginSerializer, userPhoneCheckSerializer,
                         userModelAdminGetSerializers,
                         accountsAdminUserGetDetailsSerializer, accountsAdminUserLoginSerializer,
                         accountsAdminUserGetAllSerializer, accountsAdminUserAboutGetAllSerializer,
                         accountsAdminSupervisorRegistrationSerializer,
                         accountsAdminProjectManagerSerializer, accountsAdminUserPermissionsSerializer,
                         accountsAdminProjectCoordinatorSerializer, accountsAdminHeadOfficeSerializer,
                         accountsAdminMainOwnerSerializer,
                         accountsAdminUserProfileAttendanceSerializers, accountsAdminUsersPermissionsSerializers,
                         accountsAdminUserSpecificProjectsSerializers, accountsAdminEmployeeSerializer,
                         accountsAdminSupervisorSerializer, accountsAdminStoreManagerSerializer,
                         accountsAdminGaragemanagerSerializer, userModelGetSerializers,
                         accountsAdminLoginUserAttendanceStatsSerializers, accountsAdminUserDetailUpdateSerializer,
                         accountsAdminUpdateUserProfileSerializer, )
from ..api_v1_client.serializer import accountsUserOtpLoginSerializers
from ..models import accountsUserProfileModel


# <editor-fold desc="Views For Supervisor Registration">
class accountsAdminSupervisorRegistrationGenericsView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication, BasicAuthentication, TokenAuthentication]

    def post(self, request):
        serializer = accountsAdminSupervisorRegistrationSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': "Supervisor Successfully Created"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# </editor-fold>


# <editor-fold desc="USER LOGIN WITH EMPLOYEE ID AND PASSWORD">
class accountsAdminUserLoginGenericsView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = accountsAdminUserLoginSerializer
    pagination_class = None

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_details = get_user_model().objects.get(employee_id=request.data.get('employee_id'))
        user_detail = accountsAdminUserGetDetailsSerializer(user_details).data

        response = {
            'refresh': serializer.data['refresh'],
            'access': serializer.data['access'],
            'user_detail': user_detail,
            'success': 'True',
            'status code': status.HTTP_200_OK,
            'message': 'User logged in  successfully',
        }
        status_code = status.HTTP_200_OK
        return Response(response, status=status_code)
# </editor-fold>


# <editor-fold desc="USERS AND ABOUT USER">
# <editor-fold desc="GET ALL USERS ">
class UserDepartmentFilter(django_filters.FilterSet):
    """
        by default all fields are iexact match then it will work
        below override the fields

    """

    class Meta:
        model = get_user_model()
        # exact matching bellow filed
        fields = ['is_employee', 'is_supervisor', 'is_store_manager', 'is_gaurage_manager']


# <editor-fold desc="Views For get All Users">
class accountsAdminAllUsersGenericsView(generics.ListAPIView):
    serializer_class = accountsAdminUserGetAllSerializer
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    pagination_class = LimitOffsetPagination

    search_fields = ["phone_number", "employee_id", "email"]
    filter_backends = (filters.SearchFilter, dj_filter.DjangoFilterBackend)
    filterset_class = UserDepartmentFilter

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())), many=True,
                                         context={"request": request})
        return self.get_paginated_response(serializer.data)
# </editor-fold>


# <editor-fold desc="Serializer For Get User Details And Profile Update">
class accountsAdminUserAboutDetailsAPIView(APIView):
    serializer_class = accountsAdminUserAboutGetAllSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    pagination_class = None

    def get(self, request, slug):
        try:
            data = get_user_model().objects.get(slug=slug)
        except Exception as e:
            return Response({"message": f"Data Dose Not Exist {e}", "status": status.HTTP_400_BAD_REQUEST})

        serializer = accountsAdminUserAboutGetAllSerializer(data, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # def put(self, request, slug):
    #     try:
    #         data = get_user_model().objects.get(slug=slug)
    #     except Exception as e:
    #         return Response({"message": f"Data Dose Not Exist {e}", "status": status.HTTP_400_BAD_REQUEST})
    #
    #     serializer = accountsAdminUserPermissionUpdateSerializer(data=request.data, instance=data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_200_OK)
    #     else:
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# </editor-fold>


# </editor-fold>


# <editor-fold desc="NEW SUPERVISOR CREATE">
class accountsAdminSupervisorRegistrationCreateGenericsView(generics.CreateAPIView):
    def post(self, request):
        serializer = accountsAdminSupervisorRegistrationSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': "Your Accounts is Successfully Created"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# </editor-fold>



# <editor-fold desc="Get All Users With Profiles">
class accountsAdminAllUserGenericsView(generics.ListAPIView):
    serializer_class = userModelAdminGetSerializers
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication, BasicAuthentication, TokenAuthentication]

    pagination_class = LimitOffsetPagination

    search_fields = ["phone_number", "employee_id", "email","accountsUserProfileModel_owner__name"]
    filter_backends = (filters.SearchFilter,)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())), many=True,
                                         context={"request": request})
        return self.get_paginated_response(serializer.data)


# </editor-fold>


# <editor-fold desc="Get User And Profile With Slug">
class accountsAdminAllUserGenericsDetailView(generics.GenericAPIView):
    serializer_class = userModelAdminGetSerializers
    queryset = get_user_model().objects.all()
    # permission_classes = (IsAuthenticated,)
    # authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    #
    pagination_class = LimitOffsetPagination

    search_fields = ["phone_number", "employee_id", "email"]
    filter_backends = (filters.SearchFilter,)

    def get(self, request, slug):
        query = self.queryset.filter(slug=slug).last()
        if not query:
            return Response("user not found", status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = self.serializer_class(query, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)


# </editor-fold>


# # <editor-fold desc="Post User Address With Slug">
# class accountsAdminPostUserAddressDetailView(generics.CreateAPIView):
#     serializer_class = accountsAdminUserAddressSerializer
#     queryset = accountsUserAddressModel.objects.all()
#     # permission_classes = (IsAuthenticated,)
#     # authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     search_fields = ["owner__phone_number","owner__employee_id","owner__email"]
#     filter_backends = (filters.SearchFilter,)
#
#     def post(self, request,slug):
#         serializer = accountsAdminUserAddressSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(owner=get_user_model().objects.get(slug=slug))
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# # </editor-fold>

# # <editor-fold desc="Get User Address With Slug">
# class accountsAdminAllUserAddressDetailView(generics.GenericAPIView):
#     serializer_class = accountsAdminGetUserAddressSerializer
#     queryset = accountsUserAddressModel.objects.all()
#     # permission_classes = (IsAuthenticated,)
#     # authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     search_fields = ["owner__phone_number","owner__employee_id","owner__email"]
#     filter_backends = (filters.SearchFilter,)
#
#     def get(self, request, slug):
#         query = accountsUserAddressModel.objects.filter(owner__slug=slug)
#         serializer = accountsAdminGetUserAddressSerializer(query, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)
# # </editor-fold>


# class accountsCricketContestAdminUserContestParticipationView(generics.GenericAPIView):
#     serializer_class = accountsCricketContestAdminUserContestParticipationSerializer
#     queryset = cricketContestUserContestParticipationModel.objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
#
#     def get(self, request,slug):
#         query = self.queryset.filter(user__slug=slug)
#         serializer = self.serializer_class(query, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)


# ##ALL USERS PERMISSIONS
# class accountsAdminUsersPermissionsGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminUsersPermissionsSerializers
#     queryset = get_user_model().objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     search_fields = ["phone_number",]
#     filter_backends = (filters.SearchFilter,)
#
#     def list(self,request,*args, **kwargs):
#         serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())),many=True,context={"request":request})
#         return self.get_paginated_response(serializer.data)
#
#
# class accountsAdminUsersPermissionsGenericsViewDetailsAPIView(APIView):
#     serializer_class = accountsAdminUsersPermissionsSerializers
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#     pagination_class = None
#
#     def get(self, request, slug):
#         data = get_user_model().objects.get(slug=slug)
#         serializer = accountsAdminUsersPermissionsSerializers(data)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     def put(self, request, slug):
#         data = get_user_model().objects.get(slug=slug)
#         serializer = accountsAdminUsersPermissionsSerializers(data=request.data, instance=data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data,status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def delete(self,request, slug):
#         data = get_user_model().objects.get(slug=slug)
#         data.delete()
#         return Response({"data": "Objects Deleted Successfully"}, status=status.HTTP_202_ACCEPTED)
#
#
#
# ##ENROLLMENT CHECK WITH PHONE NUMBER (if user exists are not)
# class accountsAdminLoginOtpRetrieveAPIView(APIView):
#     serializer_class = accountsAdminLoginOtpSerializers
#     permission_classes = (AllowAny,)
#
#     def post(self, request):
#         pagination_class = None
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         response = {
#             'success': 'true',
#             'status code': status.HTTP_200_OK,
#             'message': 'User logged in  successfully',
#             # 'phone': serializer.data['phone'],
#         }
#         status_code = status.HTTP_200_OK
#
#         return Response(response, status=status_code)
#
# ##SUPERVISOR CREATION
# class accountsAdminSupervisorCreationGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminSupervisorCreationSerializers
#     queryset = accountsUserProfileModel.objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     # search_fields = ["owner__email",]
#     # filter_backends = (filters.SearchFilter,)
#
#     def list(self,request,*args, **kwargs):
#         serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())),many=True,context={"request":request})
#         return self.get_paginated_response(serializer.data)
#
#     def post(self, request):
#         serializer = accountsAdminSupervisorCreationSerializers(data=request.data,context={"request":request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# ##MANAGER CREATIONS
# class accountsAdminManagerCreationGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminManagerCreationSerializers
#     queryset = accountsUserProfileModel.objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     # search_fields = ["owner__email",]
#     # filter_backends = (filters.SearchFilter,)
#
#     def list(self,request,*args, **kwargs):
#         serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())),many=True,context={"request":request})
#         return self.get_paginated_response(serializer.data)
#
#     def post(self, request):
#         serializer = accountsAdminManagerCreationSerializers(data=request.data,context={"request":request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# ##EMPLOYEE CREATION
# class accountsAdminEmployeeCreationGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminEmployeeCreationSerializers
#     queryset = accountsUserProfileModel.objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     # search_fields = ["owner__email",]
#     # filter_backends = (filters.SearchFilter,)
#
#     def list(self,request,*args, **kwargs):
#         serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())),many=True,context={"request":request})
#         return self.get_paginated_response(serializer.data)
#
#     def post(self, request):
#         serializer = accountsAdminEmployeeCreationSerializers(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# ##STORE MANAGER CREATION
# class accountsAdminStoreManagerCreationGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminStoreManagerCreationSerializers
#     queryset = accountsUserProfileModel.objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     # search_fields = ["owner__email",]
#     # filter_backends = (filters.SearchFilter,)
#
#     def list(self,request,*args, **kwargs):
#         serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())),many=True,context={"request":request})
#         return self.get_paginated_response(serializer.data)
#
#     def post(self, request):
#         serializer = accountsAdminStoreManagerCreationSerializers(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# ##ENGINEER CREATION
# class accountsAdminEngineerCreationGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminEngineerCreationSerializers
#     queryset = accountsUserProfileModel.objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     # search_fields = ["owner__email",]
#     # filter_backends = (filters.SearchFilter,)
#
#     def list(self,request,*args, **kwargs):
#         serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())),many=True,context={"request":request})
#         return self.get_paginated_response(serializer.data)
#
#     def post(self, request):
#         serializer = accountsAdminEngineerCreationSerializers(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# ##FINANCE CREATION
# class accountsAdminFinanceCreationGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminFinanceCreationSerializers
#     queryset = accountsUserProfileModel.objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     # search_fields = ["owner__email",]
#     # filter_backends = (filters.SearchFilter,)
#
#     def list(self,request,*args, **kwargs):
#         serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())),many=True,context={"request":request})
#         return self.get_paginated_response(serializer.data)
#
#     def post(self, request):
#         serializer = accountsAdminFinanceCreationSerializers(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# ##HEAD OFFICE CREATION
# class accountsAdminHeadOfficeCreationGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminHeadOfficeCreationSerializers
#     queryset = accountsUserProfileModel.objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     # search_fields = ["owner__email",]
#     # filter_backends = (filters.SearchFilter,)
#
#     def list(self,request,*args, **kwargs):
#         serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())),many=True,context={"request":request})
#         return self.get_paginated_response(serializer.data)
#
#     def post(self, request):
#         serializer = accountsAdminHeadOfficeCreationSerializers(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# ##MAIN OWNER CREATION
# class accountsAdminMainOwnerCreationGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminMainOwnerCreationSerializers
#     queryset = accountsUserProfileModel.objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     # search_fields = ["owner__email",]
#     # filter_backends = (filters.SearchFilter,)
#
#     def list(self,request,*args, **kwargs):
#         serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())),many=True,context={"request":request})
#         return self.get_paginated_response(serializer.data)
#
#     def post(self, request):
#         serializer = accountsAdminMainOwnerCreationSerializers(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_200_OK)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# # ##USER PROFILE DETAILS WITH ATTENDANCE DETAILS
# # class accountsAdminProjectsDetailsBasedAttendanceFilter(dj_filters.FilterSet):
# #     # from_date = dj_filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
# #     # to_date = dj_filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')
# #
# #     class Meta:
# #         model = attendanceUserAttendanceMainModel
# #         fields = ("attendanceProjectAttendanceUsersModel_owner__project__title",)
#
#
# class accountsAdminUserProfileAttendanceGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminUserProfileAttendanceSerializers
#     queryset = get_user_model().objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     search_fields = ["phone_number","employee_id","email","accountsUserProfileModel_user_profile__name"]
#     filter_backends = (filters.SearchFilter, dj_filters.DjangoFilterBackend)
#     # filterset_class = accountsAdminProjectsDetailsBasedAttendanceFilter
#
#     def list(self, request, *args, **kwargs):
#         filter_data = self.filter_queryset(self.get_queryset())
#         serializer = self.serializer_class(self.paginate_queryset(filter_data), many=True, context={"request": request})
#         return self.get_paginated_response(serializer.data)
#
#
# ##LOGIN USER DETAILS
# class accountsAdminUserProfileAttendanceDetailsAPIView(APIView):
#     serializer_class = accountsAdminUserProfileAttendanceSerializers
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#     pagination_class = None
#
#     def get(self, request, slug):
#         data = get_user_model().objects.get(slug=slug)
#         serializer = accountsAdminUserProfileAttendanceSerializers(data)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#
# ##LOGIN USER ATTENDANCE STATS
# class accountsAdminLoginUserAttendanceStatsGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminLoginUserAttendanceStatsSerializers
#     queryset = get_user_model().objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     search_fields = ["slug",]
#     filter_backends = (filters.SearchFilter,)
#
#     def list(self, request, *args, **kwargs):
#         filter_data = self.filter_queryset(self.get_queryset())
#         serializer = self.serializer_class(self.paginate_queryset(filter_data), many=True, context={"request": request})
#         return self.get_paginated_response(serializer.data)
#
# class accountsAdminLoginUserAttendanceStatsDetailsAPIView(APIView):
#     serializer_class = accountsAdminLoginUserAttendanceStatsSerializers
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#     pagination_class = None
#
#     def get(self, request, slug):
#         data = get_user_model().objects.get(slug=slug)
#         serializer = accountsAdminLoginUserAttendanceStatsSerializers(data)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
# ##USERS SPECIFIC LOCATION
# class accountsAdminUserSpecificProjectsGenericsView(generics.ListAPIView,generics.CreateAPIView):
#     serializer_class = accountsAdminUserSpecificProjectsSerializers
#     queryset = get_user_model().objects.all()
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#
#     pagination_class = LimitOffsetPagination
#
#     search_fields = ["slug",]
#     filter_backends = (filters.SearchFilter,)
#
#     def list(self, request, *args, **kwargs):
#         filter_data = self.filter_queryset(self.get_queryset())
#         serializer = self.serializer_class(self.paginate_queryset(filter_data), many=True, context={"request": request})
#         return self.get_paginated_response(serializer.data)
#
#
# class accountsAdminUserSpecificProjectsDetailsAPIView(APIView):
#     serializer_class = accountsAdminUserSpecificProjectsSerializers
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#     pagination_class = LimitOffsetPagination
#
#     def get(self, request, slug):
#         data = get_user_model().objects.get(slug=slug)
#         serializer = accountsAdminUserSpecificProjectsSerializers(data)
#         return Response(serializer.data, status=status.HTTP_200_OK)


# <editor-fold desc="GET WALLET WITH USER SLUG">
# class accountsAdminGetUserWalletsGenericsViewDetailsAPIView(APIView):
#     serializer_class = accountsAdminUserWalletSerializer
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
#     pagination_class = None
#
#     def get(self, request, slug):
#         try:
#             data = bitgoUserWalletModel.objects.filter(owner__slug=slug)
#         except:
#             return Response("user is not having wallet")
#         serializer = accountsAdminUserWalletSerializer(data,many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)
# </editor-fold>

# class userOtpValidationRetrieveAPIView(RetrieveAPIView):
#     permission_classes = (AllowAny,)
#     serializer_class = UserLoginSerializer
#
#     def post(self, request):
#         pagination_class = None
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         owner = get_user_model().objects.get(phone_number=serializer.data['phone'])
#         # owner = get_user_model().objects.get(email=serializer.data['email'])
#         try:
#             user_profile = accountsUserProfileModel.objects.get(user_profile=owner)
#             user_name = user_profile.name
#         except Exception as e:
#             user_name = ""
#
#         owner_serializer = userModelAdminGetSerializers(owner).data
#         weight_bridge_permission = weightBridgeUserAssignedModel.objects.filter(owner=owner)
#         if weight_bridge_permission.exists():
#             permission = weight_bridge_permission.last().type
#         else:
#             permission = None
#         # owner_profile = owner.accountsUserProfileModel_user_profile
#
#         # if owner.is_admin or owner.is_supervisor or owner.is_head_office or owner.is_main_owner == True:
#         #     access_status = True
#         # else:
#         #     access_status = False
#
#         # try:
#         #     incharge_data = attendanceUserAttendanceInChargeModel.objects.get(owner__phone_number=request.data["phone"])
#         #     all_assigned_users = incharge_data.assigned_users.all()
#         #     if len(all_assigned_users) == 0:
#         #         incharge_status = False
#         #     else:
#         #         incharge_status = True
#         # except:
#         #     incharge_status = False
#
#         # try:
#         #     referal_code = owner.accountsUserReferalCodeModel_owner.referal_code
#         # except:
#         #     accountsUserReferalCodeModel.objects.create(owner=owner,referal_code=id_generator)
#
#         serialized_data = serializer.data
#         response = {
#             "user_details": {'phone': serializer.data['phone'],
#                              'name': user_name,
#                              'email': owner.email,
#                              # 'id':owner.id,
#                              # "is_admin":owner.is_admin,
#                              # "is_employee":owner.is_employee,
#                              'main_refresh': serializer.data['refresh'],
#                              'main_access': serializer.data['access'],
#                              'owner': owner_serializer,
#
#                              'success': 'True',
#                              'status code': status.HTTP_200_OK,
#                              'message': 'User logged in  successfully',
#                              'permission': permission
#                              # 'access_permission' : access_status,
#                              # 'image':owner_profile.image.url,
#                              # 'user_details' : owner_serializer,
#                              # 'is_incharge' : incharge_status
#                              # 'image': serializer.data['image'],
#                              }}
#         status_code = status.HTTP_200_OK
#
#         return Response(response, status=status_code)




class userCreationRetrieveAPIView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserCheckAndcreationSerializer

    def post(self, request):
        pagination_class = None
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_phone = serializer.data["phone"]
        # user_mail = serializer.data["email"]
        user_name = serializer.data["name"]

        user_creation = get_user_model().objects.filter(phone_number=user_phone).last()

        # jwt_token = get_tokens_for_user(user_creation)

        # try:
        #     url = f"{base_url}accounts/api/v1/client/user-phone-password/"
        #
        #     payload = json.dumps({
        #         "phone": user_phone,
        #         "password": str(user_phone)
        #     })
        #     headers = {
        #         'Content-Type': 'application/json'
        #     }
        #
        #     response = requests.request("POST", url, headers=headers, data=payload)
        #     final_response = response.text
        #     data = json.loads(final_response)
        # except:
        #     return Response({"message":"unable to login user due to Cross origin"},status=status.HTTP_400_BAD_REQUEST)
        response = {'success': 'True',
                    'status code': status.HTTP_200_OK,
                    'message': 'User created  successfully',
                    "user_details": {'phone': user_phone,
                                     # 'email': user_mail,
                                     'name': user_name,
                                     'id': user_creation.id,
                                     'referal_code': user_creation.accountsUserReferalCodeModel_owner.referal_code},
                    # "tokens": {'main_refresh': jwt_token["refresh"],
                    #            'main_access': jwt_token["access"],
                    #            'cricket_refresh': data["refresh"],
                    #            'cricket_access': data["access"],
                    #            'success': 'True',
                    #            'status code': status.HTTP_200_OK,
                    #            'message': 'User logged in  successfully'}
                    }
        status_code = status.HTTP_200_OK

        return Response(response, status=status_code)


# <editor-fold desc="LOGIN WITH EMPLOYEE ID AND PASSWORD">
class accountsUserEmployeeIdPasswordLoginGenericsView(APIView):
    # queryset = get_user_model().objects.all()
    permission_classes = (AllowAny,)
    serializer_class = accountsUserPhonePasswordLoginSerializer
    pagination_class = None

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        owner = get_user_model().objects.get(employee_id=request.data["employee_id"])
        try:
            owner_serializer = userModelAdminGetSerializers(owner).data
        except:
            owner_serializer = {}

        try:
            owner_profile = accountsAdminUserProfileModelSerializer(owner.userProfileModel_user_profile).data
        except:
            owner_profile = {}

        try:
            url = f"{base_url}accounts/api/v1/admin/employee_id-with-phone/{owner.phone_number}"

            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request("GET", url, headers=headers)
            final_response = response.text
            employee_id = json.loads(final_response)

            url = f"{base_url}accounts/api/v1/admin/employee_id-password-login/"

            payload = json.dumps({
                "employee_id": employee_id,
                "password": owner.phone_number
            })
            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            final_response = response.text
            data = json.loads(final_response)
            print(data)
        except Exception as e:
            print(e)
            return Response({"message": "unable to login user due to Cross origin"}, status=status.HTTP_400_BAD_REQUEST)

        response = {
            'success': 'True',
            'status code': status.HTTP_200_OK,
            'message': 'User logged in  successfully',
            # 'refresh': serializer.data['refresh'],
            # 'access': serializer.data['access'],
            'user_details': owner_serializer,
            'profile': owner_profile,

            'tokens': {'main_refresh': serializer.data['refresh'],
                       'main_access': serializer.data['access'],
                       'cricket_refresh': data["refresh"],
                       'cricket_access': data["access"],
                       'success': 'True',
                       'status code': status.HTTP_200_OK,
                       'message': 'User logged in  successfully'}}
        status_code = status.HTTP_200_OK
        return Response(response, status=status_code)


# </editor-fold>


# <editor-fold desc="Views For get Total User Stats">
class accountsAdminBasicUserStatsGenericsView(generics.ListAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication, BasicAuthentication, TokenAuthentication]

    def get(self, request):
        details = {}
        details["total_technicians"] = get_user_model().objects.filter(is_supervisor=True).count()
        details["total_active_technicians"] = get_user_model().objects.filter(
            is_supervisor=True, is_active=True).count()
        details["total_inactive_technicians"] = get_user_model().objects.filter(
            is_supervisor=True, is_active=False).count()
        details["total_leaves"] = 0
        return Response(details, status=status.HTTP_200_OK)
# </editor-fold>


# """
# user otp validation
# """
# class userOtpValidationRetrieveAPIView(RetrieveAPIView):
#
#     permission_classes = (AllowAny,)
#     serializer_class = UserLoginSerializer
#
#     def post(self, request):
#         pagination_class = None
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         owner = get_user_model().objects.get(phone_number=serializer.data['phone'])
#         print(owner)
#         owner_serializer = accountsUserOtpLoginSerializers(owner).data
#         owner_profile = owner.accountsUserProfileModel_owner
#
#         if owner.is_admin or owner.is_supervisor or owner.is_head_officer or owner.is_main_owner == True:
#             access_status = True
#         else:
#             access_status = False
#
#         try:
#             incharge_data = attendanceUserAttendanceInChargeModel.objects.get(owner__phone_number=request.data["phone"])
#             all_assigned_users = incharge_data.assigned_users.all()
#             if len(all_assigned_users) == 0:
#                 incharge_status = False
#             else:
#                 incharge_status = True
#         except:
#             incharge_status = False
#
#         response = {
#             'success' : 'True',
#             'status code' : status.HTTP_200_OK,
#             'message': 'User logged in  successfully',
#             'refresh' : serializer.data['refresh'],
#             'access': serializer.data['access'],
#             'phone': serializer.data['phone'],
#             'name': owner_profile.name,
#             'access_permission' : access_status,
#             'image':owner_profile.image.url,
#             'user_details' : owner_serializer,
#             'is_incharge' : incharge_status
#             # 'image': serializer.data['image'],
#             }
#         status_code = status.HTTP_200_OK
#
#         return Response(response, status=status_code)
#
#
"""
user otp validation
"""
# class userOtpValidationRetrieveAPIView(RetrieveAPIView):
#
#     permission_classes = (AllowAny,)
#     serializer_class = UserLoginSerializer
#
#     def post(self, request):
#         pagination_class = None
#         serializer = self.serializer_class(data=request.data)
#         serializer.is_valid(raise_exception=True)
#
#         owner = get_user_model().objects.get(phone_number=serializer.data['phone'])
#         owner_serializer = accountsAdminUserOtpLoginSerializers(owner).data
#         owner_profile = owner.accountsUserProfileModel_owner
#
#         if owner.is_admin or owner.is_supervisor or owner.is_head_office or owner.is_main_owner == True:
#             access_status = True
#         else:
#             access_status = False
#
#         try:
#             incharge_data = attendanceUserAttendanceInChargeModel.objects.get(owner__phone_number=request.data["phone"])
#             all_assigned_users = incharge_data.assigned_users.all()
#             if len(all_assigned_users) == 0:
#                 incharge_status = False
#             else:
#                 incharge_status = True
#         except:
#             incharge_status = False
#
#         response = {
#             'success' : 'True',
#             'status code' : status.HTTP_200_OK,
#             'message': 'User logged in  successfully',
#             'refresh' : serializer.data['refresh'],
#             'access': serializer.data['access'],
#             'phone': serializer.data['phone'],
#             'name': owner_profile.name,
#             'access_permission' : access_status,
#             'image':owner_profile.image.url,
#             'user_details' : owner_serializer,
#             'is_incharge' : incharge_status
#             # 'image': serializer.data['image'],
#             }
#         status_code = status.HTTP_200_OK
#
#         return Response(response, status=status_code)
"""
user otp validation
"""
class userOtpValidationRetrieveAPIView(RetrieveAPIView):

    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer

    def post(self, request):
        pagination_class = None
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        owner = get_user_model().objects.get(phone_number=serializer.data['phone'])
        owner_serializer = accountsUserOtpLoginSerializers(owner).data
        owner_profile = owner.accountsUserProfileModel_owner

        if owner.is_admin or owner.is_supervisor or owner.is_head_office or owner.is_main_owner == True:
            access_status = True
        else:
            access_status = False

        try:
            incharge_data = attendanceUserAttendanceInChargeModel.objects.get(owner__phone_number=request.data["phone"])
            all_assigned_users = incharge_data.assigned_users.all()
            if len(all_assigned_users) == 0:
                incharge_status = False
            else:
                incharge_status = True
        except:
            incharge_status = False

        response = {
            'success' : 'True',
            'status code' : status.HTTP_200_OK,
            'message': 'User logged in  successfully',
            'refresh' : serializer.data['refresh'],
            'access': serializer.data['access'],
            'phone': serializer.data['phone'],
            'name': owner_profile.name,
            'access_permission' : access_status,
            'image':owner_profile.image.url,
            'user_details' : owner_serializer,
            'is_incharge' : incharge_status
            # 'image': serializer.data['image'],
            }
        status_code = status.HTTP_200_OK

        return Response(response, status=status_code)



# <editor-fold desc="View For Get All User permissions and Update">
class accountsAdminUserPermissionDetailsAPIView(APIView):
    serializer_class = accountsAdminUserPermissionsSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    pagination_class = None

    def get(self, request, slug):
        try:
            data = get_user_model().objects.get(slug=slug)
        except:
            return Response({"message": f"User Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        serializer = accountsAdminUserPermissionsSerializer(data, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, slug):
        try:
            data = get_user_model().objects.get(slug=slug)
        except:
            return Response({"message": f"User Doesn't Exist", "status": status.HTTP_400_BAD_REQUEST})

        serializer = accountsAdminUserPermissionsSerializer(data=request.data, instance=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# </editor-fold>



"""
user phone check 
"""
class userPhoneCheckRetrieveAPIView(RetrieveAPIView):

    permission_classes = (AllowAny,)
    serializer_class = userPhoneCheckSerializer

    def post(self, request):
        pagination_class = None

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = {
            'status code' : status.HTTP_200_OK,
            'result' : serializer.data['data'],
            }
        status_code = status.HTTP_200_OK

        return Response(response, status=status_code)


# class accountsAdminViewUserAboutDetailsAPIView(APIView):
#     serializer_class = accountsAdminViewUserDetailSerializer
#     permission_classes = (IsAuthenticated,)
#     authenticate_class = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
#     pagination_class = None
#
#     def get(self, request, slug):
#         try:
#             data = get_user_model().objects.get(slug=slug)
#         except Exception as e:
#             return Response({"message": f"Data Dose Not Exist {e}", "status": status.HTTP_400_BAD_REQUEST})
#
#         serializer = accountsAdminViewUserDetailSerializer(data, context={"request": request})
#         return Response(serializer.data, status=status.HTTP_200_OK)
#


# <editor-fold desc="user profile with attendance data">
class accountsAdminUserProfileAttendanceGenericsView(generics.ListAPIView,generics.CreateAPIView):
    serializer_class = accountsAdminUserProfileAttendanceSerializers
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]

    pagination_class = LimitOffsetPagination

    search_fields = ["phone_number","employee_id","email","accountsUserProfileModel_owner__first_name","accountsUserProfileModel_owner__last_name",]
    filter_backends = (filters.SearchFilter, dj_filter.DjangoFilterBackend)
    # filterset_class = accountsAdminProjectsDetailsBasedAttendanceFilter

    # def list(self,request,*args, **kwargs):
    #     serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())),many=True,context={"request":request})
    #     return self.get_paginated_response(serializer.data)
    #

    def list(self, request, *args, **kwargs):
        filter_data = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(self.paginate_queryset(filter_data), many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)
# </editor-fold>

# <editor-fold desc="ALL USERS PERMISSIONS">
class accountsAdminUsersPermissionsGenericsView(generics.ListAPIView,generics.CreateAPIView):
    serializer_class = accountsAdminUsersPermissionsSerializers
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]

    pagination_class = LimitOffsetPagination

    search_fields = ["phone_number",]
    filter_backends = (filters.SearchFilter,)

    def list(self,request,*args, **kwargs):
        serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())),many=True,context={"request":request})
        return self.get_paginated_response(serializer.data)


class accountsAdminUsersPermissionsGenericsViewDetailsAPIView(APIView):
    serializer_class = accountsAdminUsersPermissionsSerializers
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def get(self, request, slug):
        try:
            data = get_user_model().objects.get(slug=slug)
        except:
            return Response({"message": "User does not Exists"}, status=status.HTTP_200_OK)

        serializer = accountsAdminUsersPermissionsSerializers(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, slug):
        try:
            data = get_user_model().objects.get(slug=slug)
        except:
            return Response({"message": "User does not Exists"}, status=status.HTTP_200_OK)

        serializer = accountsAdminUsersPermissionsSerializers(data=request.data, instance=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request, slug):
        try:
            data = get_user_model().objects.get(slug=slug)
        except:
            return Response({"message": "User does not Exists"}, status=status.HTTP_200_OK)

        data.delete()
        return Response({"data": "Objects Deleted Successfully"}, status=status.HTTP_202_ACCEPTED)
# </editor-fold>



##USERS SPECIFIC LOCATION
# <editor-fold desc="Description">
class accountsAdminUserSpecificProjectsGenericsView(generics.ListAPIView,generics.CreateAPIView):
    serializer_class = accountsAdminUserSpecificProjectsSerializers
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]

    pagination_class = LimitOffsetPagination

    search_fields = ["slug",]
    filter_backends = (filters.SearchFilter,)

    def list(self, request, *args, **kwargs):
        filter_data = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(self.paginate_queryset(filter_data), many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)
# </editor-fold>


# <editor-fold desc="USERS SPECIFIC PROJECTS UPDATE">
class accountsAdminUserSpecificProjectsDetailsAPIView(APIView):
    serializer_class = accountsAdminUserSpecificProjectsSerializers
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = LimitOffsetPagination

    def get(self, request, slug):
        try:
            data = get_user_model().objects.get(slug=slug)
        except:
            return Response({"message": "User does not Exists"}, status=status.HTTP_200_OK)

        serializer = accountsAdminUserSpecificProjectsSerializers(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
# </editor-fold>



# <editor-fold desc="view for project manager New create">
class accountAdminProjectManagerGenericApiView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = accountsAdminProjectManagerSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [BasicAuthentication, SessionAuthentication, TokenAuthentication,JWTAuthentication]

    def post(self, request, *args, **kwargs):

        serializer = accountsAdminProjectManagerSerializer(data=request.data,
                                                      context={"request": request, })
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Project Manager Created Successfully", 'status': status.HTTP_200_OK})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# </editor-fold>

# <editor-fold desc="view for Project Coordinator create">
class accountAdminProjectCoordinatorGenericApiView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = accountsAdminProjectCoordinatorSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [BasicAuthentication, SessionAuthentication, TokenAuthentication,JWTAuthentication]

    def post(self, request, *args, **kwargs):

        serializer = accountsAdminProjectCoordinatorSerializer(data=request.data,
                                                          context={"request": request, })
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Project Coordinator Created Successfully", 'status': status.HTTP_200_OK})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# </editor-fold>

# <editor-fold desc="view for Head Officer create">
class accountAdminHeadOfficeGenericApiView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = accountsAdminHeadOfficeSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [BasicAuthentication, SessionAuthentication, TokenAuthentication,JWTAuthentication]

    def post(self, request, *args, **kwargs):

        serializer = accountsAdminHeadOfficeSerializer(data=request.data,
                                                   context={"request": request, })
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Head Officer Created Successfully", 'status': status.HTTP_200_OK})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# </editor-fold>

# <editor-fold desc="view for Main Owner create">
class accountAdminMainOwnerGenericApiView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = accountsAdminMainOwnerSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [BasicAuthentication, SessionAuthentication, TokenAuthentication,JWTAuthentication]

    def post(self, request, *args, **kwargs):
        serializer = accountsAdminMainOwnerSerializer(data=request.data,context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Main Owner Created Successfully", 'status': status.HTTP_200_OK})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# </editor-fold>

# <editor-fold desc="view for employee New create">
class accountAdminEmployeeGenericApiView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = accountsAdminEmployeeSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [BasicAuthentication, SessionAuthentication, TokenAuthentication, JWTAuthentication]

    def post(self, request, *args, **kwargs):

        serializer = accountsAdminEmployeeSerializer(data=request.data,
                                                      context={"request": request, })
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Employee Created Successfully", 'status': status.HTTP_200_OK})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# </editor-fold>

# <editor-fold desc="view for Supervisor New create">
class accountAdminSupervisorGenericApiView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = accountsAdminSupervisorSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [BasicAuthentication, SessionAuthentication, TokenAuthentication, JWTAuthentication]

    def post(self, request, *args, **kwargs):

        serializer = accountsAdminSupervisorSerializer(data=request.data,
                                                      context={"request": request, })
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Supervisor Created Successfully", 'status': status.HTTP_200_OK})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# </editor-fold>

# <editor-fold desc="view for Store manager New create">
class accountAdminStoremanagerGenericApiView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = accountsAdminStoreManagerSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [BasicAuthentication, SessionAuthentication, TokenAuthentication, JWTAuthentication]

    def post(self, request, *args, **kwargs):

        serializer = accountsAdminStoreManagerSerializer(data=request.data,
                                                      context={"request": request, })
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Store Manager Created Successfully", 'status': status.HTTP_200_OK})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# </editor-fold>

# <editor-fold desc="view for Garage manager New create">
class accountAdminGarageManagerGenericApiView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = accountsAdminGaragemanagerSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = [BasicAuthentication, SessionAuthentication, TokenAuthentication, JWTAuthentication]

    def post(self, request, *args, **kwargs):

        serializer = accountsAdminGaragemanagerSerializer(data=request.data,
                                                      context={"request": request, })
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Garage Manager Created Successfully", 'status': status.HTTP_200_OK})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# </editor-fold>


# <editor-fold desc="All users">
"""
all users serializers
"""

class allUserGenericsView(generics.ListAPIView,generics.CreateAPIView):
    serializer_class = userModelGetSerializers
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]

    pagination_class = LimitOffsetPagination

    search_fields = ["phone_number","employee_id","email","accountsUserProfileModel_owner__name"]
    filter_backends = (filters.SearchFilter,)

    def list(self,request,*args, **kwargs):
        serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())), many=True,
                                         context={"request": request})
        return self.get_paginated_response(serializer.data)
# </editor-fold>


# <editor-fold desc="login user attendance">
class accountsAdminLoginUserAttendanceStatsDetailsAPIView(APIView):
    serializer_class = accountsAdminLoginUserAttendanceStatsSerializers
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def get(self, request, slug):
        try:
            data = get_user_model().objects.get(slug=slug)
        except:
            return Response({"message": "User does not Exists"}, status=status.HTTP_200_OK)

        serializer = accountsAdminLoginUserAttendanceStatsSerializers(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
# </editor-fold>


# <editor-fold desc="Login user detail">
##LOGIN USER DETAILS
class accountsAdminUserProfileAttendanceDetailsAPIView(APIView):
    serializer_class = accountsAdminUserProfileAttendanceSerializers
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def get(self, request, slug):
        try:
            data = get_user_model().objects.get(slug=slug)
        except:
            return Response({"message":"User does not Exists"}, status=status.HTTP_200_OK)
        serializer = accountsAdminUserProfileAttendanceSerializers(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
# </editor-fold>



# new add user phone number and email

# <editor-fold desc="User phone number and email">
class accountsAdminUserDetailsAPIView(APIView):
    serializer_class = accountsAdminUserDetailUpdateSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    pagination_class = None

    def put(self, request, slug):
        try:
            data = get_user_model().objects.get(slug=slug)
        except Exception as e:
            return Response({"message": f"Data Dose Not Exist {e}", "status": status.HTTP_400_BAD_REQUEST})

        serializer = accountsAdminUserDetailUpdateSerializer(data=request.data, instance=data, partial=True,context={"request": request, })
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Employee phone and email Successfully Updated."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# </editor-fold>


# <editor-fold desc="View For User Profile Update">
class accountsAdminUserProfileUpdateDetailsAPIView(APIView):
    serializer_class = accountsAdminUpdateUserProfileSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def put(self, request, slug):
        try:
            data = accountsUserProfileModel.objects.get(owner__slug=slug)
        except:
            return Response({"message":"User Does not Exist","status":status.HTTP_400_BAD_REQUEST})
        serializer = accountsAdminUpdateUserProfileSerializer(data=request.data, instance=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# </editor-fold>