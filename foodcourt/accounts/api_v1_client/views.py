from django.contrib.auth.models import update_last_login
from django.utils.datetime_safe import datetime
from rest_framework import status
from django_filters import rest_framework as dj_filters
import random
from rest_framework.generics import RetrieveAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializer import *
# from .serializer import accountsClientUsersSearchSerializer,accountsClientLoginUserProfileSerializer,accountsClientLoginUserDetailsSerializer,accountsUserOtpLoginSerializers,accountsUserProfileSerializers,accountsCommonUserSerializers,UserLoginSerializer,userPhoneCheckSerializer,UserEnrollmentSerializer,userModelGetSerializers, TiarPostAPIModelSerializer
from rest_framework.authentication import TokenAuthentication,SessionAuthentication,BasicAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework import status, generics,filters
from rest_framework.pagination import LimitOffsetPagination
from django.contrib.auth import get_user_model, authenticate
from ..models import accountsUserLoginOtpModel,accountsUserProfileModel,accountsAdminUserCreationLoginOtpModel
from srk_projects_core.twillo import send_message_otp
from django.core.mail import send_mail
import requests
from django.conf import settings

#
class allUserGenericsView(generics.ListAPIView,generics.CreateAPIView):
    serializer_class = userModelGetSerializers
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]

    pagination_class = LimitOffsetPagination

    search_fields = ["phone_number","employee_id","email"]
    filter_backends = (filters.SearchFilter,)

    def list(self,request,*args, **kwargs):
        serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())), many=True,
                                         context={"request": request})
        return self.get_paginated_response(serializer.data)


"""
user phone check 
"""
class userPhoneCheckRetrieveAPIView(RetrieveAPIView):
    queryset = get_user_model().objects.all()
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


class userEmailCheckRetrieveAPIView(RetrieveAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = (AllowAny,)
    serializer_class = userEmailCheckSerializer

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

# class userPhoneCheckAPIView(APIView):
#     def post(self, request):
#         try:
#             data = get_user_model().objects.filter(phone_number=request.data["phone_number"])
#             # serializer = userCardDetailsSerializers(data)
#             if data:
#                 return Response({'result':True}, status=status.HTTP_200_OK)
#             else:
#                 return Response({'result':False}, status=status.HTTP_200_OK)
#         except:
#             return Response({'result':False}, status=status.HTTP_400_BAD_REQUEST)

import json


# <editor-fold desc="USER PHONE NUMBER SEND OTP">
class accountsAdminSendOtpForUserCreationAPIView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        phone = request.data["phone"]
        user = get_user_model().objects.filter(phone_number=phone)
        if len(user) == 0:
            final_otp = random.randint(1000, 9999)
            try:
                send_message_otp(phone, final_otp)
            except:
                return Response({"message":"unable to send otp"}, status=status.HTTP_400_BAD_REQUEST)
            accountsAdminUserCreationLoginOtpModel.objects.create(phone_number=phone, otp=final_otp, active=True)
            response = {
            'success': 'true',
            'status code': status.HTTP_200_OK,
            'message': 'User checked in  successfully',
            'phone': phone,
        }
            status_code = status.HTTP_200_OK
            return Response(response, status=status_code)
        else:
            response = {
                'success': 'false',
                'status code': status.HTTP_400_BAD_REQUEST,
                'message': 'user with this number already exists',
                'phone': phone,
            }
            status_code = status.HTTP_400_BAD_REQUEST
            return Response(response, status=status_code)
# </editor-fold>



# <editor-fold desc="USER EMAIL SEND OTP ">
class accountsAdminSendOtpForUserCreationToEmailAPIView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data["email"]
        user = get_user_model().objects.filter(email=email)
        if len(user) == 0:
            final_otp = random.randint(1000, 9999)
            send_mail(
                'The Otp received From Tiar',
                f'The Otp To Create An Account In Tiar Is {final_otp}',
                'info@techarion.com',
                [email],
                fail_silently=False,
            )
            # send_message_otp(phone, final_otp)
            accountsAdminUserCreationLoginOtpModel.objects.create(email=email, otp=final_otp, active=True)
            response = {
            'success': 'true',
            'status code': status.HTTP_200_OK,
            'message': 'User checked in  successfully',
            'email': email,
        }
            status_code = status.HTTP_200_OK
            return Response(response, status=status_code)
        else:
            response = {
                'success': 'false',
                'status code': status.HTTP_400_BAD_REQUEST,
                'message': 'user with this email already exists',
                'email': email,
            }
            status_code = status.HTTP_400_BAD_REQUEST
            return Response(response, status=status_code)
# </editor-fold>
"""
user otp validation
"""


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
class userOtpValidationRetrieveAPIView(RetrieveAPIView):

    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer

    def post(self, request):
        pagination_class = None
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        owner = get_user_model().objects.get(phone_number=serializer.data['phone'])
        # owner = get_user_model().objects.get(email=serializer.data['email'])
        try:
            user_profile = accountsUserProfileModel.objects.get(user_profile=owner)
            user_name = user_profile.name
        except Exception as e:
            user_name = ""

        # owner_serializer = accountsUserOtpLoginSerializers(owner).data
        # owner_profile = owner.accountsUserProfileModel_user_profile

        # if owner.is_admin or owner.is_supervisor or owner.is_head_office or owner.is_main_owner == True:
        #     access_status = True
        # else:
        #     access_status = False

        # try:
        #     incharge_data = attendanceUserAttendanceInChargeModel.objects.get(owner__phone_number=request.data["phone"])
        #     all_assigned_users = incharge_data.assigned_users.all()
        #     if len(all_assigned_users) == 0:
        #         incharge_status = False
        #     else:
        #         incharge_status = True
        # except:
        #     incharge_status = False

        try:
            referal_code = owner.accountsUserReferalCodeModel_owner.referal_code
        except:
            name = owner.accountsUserProfileModel_user_profile.name
            splited_name = name.split()
            code = splited_name[0].upper() + str(owner.id) + get_random_string(5,string.ascii_uppercase + string.digits)
            accountsUserReferalCodeModel.objects.create(owner=owner,referal_code=code)

        serialized_data = serializer.data
        cric_refresh_token = serialized_data['cricket_refresh']
        cric_access_token = serialized_data['cricket_access']
        response = {
            "user_details":{'phone': serializer.data['phone'],
                            'name': user_name,
                            'email':owner.email,
                            'id':owner.id,

                            'referal_code':owner.accountsUserReferalCodeModel_owner.referal_code},
            "tokens": {'main_refresh' : serializer.data['refresh'],
                        'main_access': serializer.data['access'],
                        'cricket_refresh':cric_refresh_token,
                        'cricket_access':cric_access_token},
            'success' : 'True',
            'status code' : status.HTTP_200_OK,
            'message': 'User logged in  successfully',
            # 'access_permission' : access_status,
            # 'image':owner_profile.image.url,
            # 'user_details' : owner_serializer,
            # 'is_incharge' : incharge_status
            # 'image': serializer.data['image'],
            }
        status_code = status.HTTP_200_OK

        return Response(response, status=status_code)



class userEmailOtpValidationRetrieveAPIView(RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserEmailOtpLoginSerializer

    def post(self, request):
        pagination_class = None
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        owner = get_user_model().objects.get(email=serializer.data['email'])
        user_profile = accountsUserProfileModel.objects.get(user_profile=owner)

        response = {
            'success' : 'True',
            'status code' : status.HTTP_200_OK,
            'message': 'User logged in  successfully',
            'refresh' : serializer.data['refresh'],
            'access': serializer.data['access'],
            'email': serializer.data['email'],
            'name': user_profile.name,
            'referal_code':owner.accountsUserReferalCodeModel_owner.referal_code
            }
        status_code = status.HTTP_200_OK

        return Response(response, status=status_code)


class accountsUserLoginGenericsView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = accountsEmailLoginSerializer
    pagination_class = None

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        owner = get_user_model().objects.get(email=serializer.data['email'])
        try:
            owner_serializer = userModelGetSerializers(owner).data
        except:
            owner_serializer = {}

        # try:
        #     owner_profile = accountsAdminGetLoginUserprofileSerializer(owner.accountsUserProfileModel_user_profile).data
        # except:
        #     owner_profile = {}

        response = {
            'success': 'True',
            'status code': status.HTTP_200_OK,
            'message': 'User logged in  successfully',
            'refresh': serializer.data['refresh'],
            'access': serializer.data['access'],
            'user_details': owner_serializer,
            # 'profile': owner_profile,
        }
        status_code = status.HTTP_200_OK
        return Response(response, status=status_code)


###USER OTP CHECK
class userOtpCheckAPIView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        phone = request.data["phone"]
        otp = request.data["otp"]
        otp_check = accountsAdminUserCreationLoginOtpModel.objects.filter(phone_number=phone, otp=otp,
                                                                          active=True).last()
        if otp_check:
            return Response({"status":True,"phone":phone})
        else:
            return Response({"status":False,"phone":phone})


class userEmailOtpCheckAPIView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data["email"]
        otp = request.data["otp"]
        otp_check = accountsAdminUserCreationLoginOtpModel.objects.filter(email=email, otp=otp,
                                                                          active=True).last()
        if otp_check:
            return Response({"status":True,"email":email})
        else:
            return Response({"status":False,"email":email})


class userCreationRetrieveAPIView(RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserCheckAndcreationSerializer

    def post(self, request):
        pagination_class = None
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_phone = serializer.data["phone"]
        # user_mail = serializer.data["email"]
        user_name = serializer.data["name"]

        user_creation = get_user_model().objects.filter(phone_number=user_phone).last()

        jwt_token = get_tokens_for_user(user_creation)

        try:
            url = f"{base_url}accounts/api/v1/client/user-phone-password/"

            payload = json.dumps({
                "phone": user_phone,
                "password": str(user_phone)
            })
            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            final_response = response.text
            data = json.loads(final_response)
        except:
            return Response({"message":"unable to login user due to Cross origin"},status=status.HTTP_400_BAD_REQUEST)
        response = {'success': 'True',
                    'status code': status.HTTP_200_OK,
                    'message': 'User logged in  successfully',
            "user_details": {'phone': user_phone,
                             # 'email': user_mail,
                             'name': user_name,
                             'id': user_creation.id,
                             'referal_code': user_creation.accountsUserReferalCodeModel_owner.referal_code},
            "tokens": {'main_refresh': jwt_token["refresh"],
                       'main_access': jwt_token["access"],
                       'cricket_refresh': data["refresh"],
                       'cricket_access': data["access"],
                       'success': 'True',
                       'status code': status.HTTP_200_OK,
                       'message': 'User logged in  successfully'}
        }
        status_code = status.HTTP_200_OK

        return Response(response, status=status_code)


class userCreationEmailRetrieveAPIView(RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserCheckAndcreationWithEmailSerializer

    def post(self, request):
        pagination_class = None
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_user_model().objects.filter(email=serializer.data["email"]).last()
        response = {
            'success' : 'True',
            'status code' : status.HTTP_200_OK,
            'message': 'User logged in  successfully',
            'refresh': serializer.data['refresh'],
            'access': serializer.data['access'],
            'email': serializer.data['email'],
            'name': user.accountsUserProfileModel_user_profile.name,
            'referal_code': user.accountsUserReferalCodeModel_owner.referal_code
            }
        status_code = status.HTTP_200_OK

        return Response(response, status=status_code)


class accountsEnrollmentRetrieveAPIView(APIView):
    serializer_class = UserEnrollmentSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        pagination_class = None
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # print(serializer.data['phone'])
        if serializer.data['check']:
            response = {
                'success' : 'true',
                'status code' : status.HTTP_200_OK,
                'message': 'User logged in  successfully',
                'phone' : serializer.data['phone'],
                }
            status_code = status.HTTP_200_OK

        else:
            response = {
                'success': 'false',
                'status code': status.HTTP_208_ALREADY_REPORTED,
                'message': "user with this number already exists",
                'phone': serializer.data['phone'],
            }
            status_code = status.HTTP_208_ALREADY_REPORTED

        return Response(response, status=status_code)


class accountsClientGetAllReferalCodesGenericAPIView(generics.ListAPIView):
    queryset = accountsUserReferalCodeModel.objects.all()
    serializer_class = accountsClientGetAllReferalCodesSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = LimitOffsetPagination


    def list(self, request,*args, **kwargs):
        serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset())), many=True,
                                         context={"request": request})
        return self.get_paginated_response(serializer.data)


# <editor-fold desc="UPDATE USER PROFILE NAME">
class accountsClientUserProfileUpdateDetailsAPIView(APIView):
    serializer_class = accountsClientUpdateUserProfileSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def put(self, request, slug):
        data = accountsUserProfileModel.objects.get(user_profile__slug=slug)
        serializer = accountsClientUpdateUserProfileSerializer(data=request.data, instance=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# </editor-fold>

# <editor-fold desc="UPDATE USER IMAGE">
class accountsClientUserProfileUpdateImageDetailsAPIView(APIView):
    serializer_class = accountsClientUpdateUserProfileImageSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def put(self, request, slug):
        data = accountsUserProfileModel.objects.get(user_profile__slug=slug)
        serializer = accountsClientUpdateUserProfileImageSerializer(data=request.data, instance=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# </editor-fold>


class accountsClientLoginUserDetailsDetailsAPIView(APIView):
    serializer_class = accountsClientUserDetailsSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def get(self, request):
        data = get_user_model().objects.get(email=request.user.email)
        serializer = accountsClientUserDetailsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class accountsClientUserProfileDetailsAPIView(APIView):
    serializer_class = accountsClientUserProfileUpdateSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def put(self, request):
        data = accountsUserProfileModel.objects.get(user_profile=request.user)
        serializer = accountsClientUserProfileUpdateSerializer(data=request.data, instance=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class accountsClientUserProfileImageUpdateDetailsAPIView(APIView):
    serializer_class = accountsClientUserProfileUpdateImageSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def put(self, request):
        data = accountsUserProfileModel.objects.get(user_profile=request.user)
        serializer = accountsClientUserProfileUpdateImageSerializer(data=request.data, instance=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class userPhoneUpdateSendOtpAPIView(RetrieveAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    serializer_class = userPhoneUpdateSendOtpSerializer

    def post(self, request):
        data = request.data
        data["user"]=request.user

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        response = {
            'status code' : status.HTTP_200_OK,
            'result' : serializer.data['data'],
            'phone': serializer.data['phone'],
            }
        status_code = status.HTTP_200_OK
        return Response(response, status=status_code)


class accountsClientUserPhoneUpdateGenericsView(RetrieveAPIView):
    serializer_class = accountsClientUserPhoneUpdateSerializer
    # queryset = kycUserPhoneOtpVerificationModel.objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]

    def post(self, request):
        data = request.data
        data["user"]=request.user
        serializer = accountsClientUserPhoneUpdateSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.data["data"] == "True":
                return Response({"message":"success"}, status=status.HTTP_200_OK)
            else:
                return Response({"message":"please enter valid otp"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class accountClientEmailUpdateOtpRetrieveAPIView(RetrieveAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    serializer_class = accountsClientEmailUpdateOtpSerializer

    def post(self, request):
        pagination_class = None
        data = request.data
        data["user"]=request.user

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = {
            'status code' : status.HTTP_200_OK,
            'result' : serializer.data['data'],
            }
        status_code = status.HTTP_200_OK
        return Response(response, status=status_code)


class accountsClientUserEmailUpdateGenericsView(RetrieveAPIView):
    serializer_class = accountsClientUserEmailUpdateSerializer
    # queryset = kycUserPhoneOtpVerificationModel.objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]

    def post(self, request):
        data = request.data
        data["user"]=request.user
        serializer = accountsClientUserEmailUpdateSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.data["data"] == "True":
                return Response({"message":"success"}, status=status.HTTP_200_OK)
            else:
                return Response({"message":"please enter valid otp"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class accountsClientAddAddressGenericsView(generics.ListAPIView,generics.CreateAPIView):
    serializer_class = accountsClientAddAddressSerializer
    queryset = accountsUserAddressModel.objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]

    def post(self, request):
        serializer = accountsClientAddAddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class accountsClientUserAddressUpdateAndGetDetailsAPIView(APIView):
    serializer_class = accountsClientAddAddressSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def get(self,request):
        try:
            data = accountsUserAddressModel.objects.filter(owner=request.user).last()
            serializer = accountsClientGetUserAddressSerializer(data)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response(f"somthing went wrong{e}")

    def put(self, request):
        data = accountsUserAddressModel.objects.filter(owner=request.user).last()
        serializer = accountsClientAddAddressSerializer(data=request.data, instance=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class accountsClientUserInfoDetailsAPIView(APIView):
    serializer_class = accountsClientAddAddressSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def get(self,request):
        try:
            user = request.user
            data = accountsUserProfileModel.objects.filter(user_profile=request.user).last()
            serializer = accountsClientUserInfoSerializer(user)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response(f"somthing went wrong{e}")


# <editor-fold desc="GET USER PROFILE">
class accountsClientUserProfileInfoDetailsAPIView(APIView):
    serializer_class = accountsClientUserInfoSerializer
    # permission_classes = (IsAuthenticated,)
    # authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def get(self,request,phone_number):
        try:
            user = get_user_model().objects.filter(phone_number=phone_number).first()
            serializer = accountsClientUserInfoSerializer(user)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response(f"somthing went wrong{e}")
# </editor-fold>


# <editor-fold desc="GET USER Complete STATS">
class accountsClientUserPlayedCompleteDetailsAPIView(APIView):
    serializer_class = accountsClientUserInfoSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def get(self,request):
        login_user = request.user

        # <editor-fold desc="USER CRICKET STATS">
        try:
            url = f"{base_url}cricketfantasy/api/v2/client/user-profile-played-stats/{login_user.phone_number}/"
            payload = {}
            headers = {
                # 'Authorization': 'Basic MDow'
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            cricket_data = json.loads(response.text)
        except Exception as e:
            return Response({"message":"Failed to load cricket api"},status=status.HTTP_400_BAD_REQUEST)
        # </editor-fold>
        final_result = {}
        try:
            final_result["contests"] = cricket_data["contests"]
        except Exception as e:
            return Response({"message": "No response from cricket database"},status=status.HTTP_400_BAD_REQUEST)
        if cricket_data["contests"] > 1:
            final_result["sports"] = 1
        final_result["matches"] = cricket_data["matches"]
        final_result["series"] = cricket_data["series"]
        final_result["win_rate"] = round(cricket_data["win_rate"],2)
        final_result["public"] = cricket_data["public"]
        final_result["private"] = cricket_data["private"]
        return Response(final_result)
# </editor-fold>


# <editor-fold desc="User profile stats">
class accountsClientUserProfileSkillScoreDetailsAPIView(APIView):
    serializer_class = accountsClientUserProfileInfoSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def get(self,request):
        try:
            main_user = request.user.accountsUserProfileModel_user_profile
            serializer = accountsClientUserProfileInfoSerializer(main_user)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            final_data = {
                "user_profile": "",
                "skill_score": {
                    "id": 0,
                    "owner": 0,
                    "cricket_score": 0,
                    "football_score": 0,
                    "kabaddi_score": 0,
                    "backetball_score": 0,
                    "baseball_score": 0,
                    "volleyball_score": 0,
                    "handball_score": 0,
                    "slug": ""
                },
                "image": "",
                "name": "",
                "user_game_name": "",
                "gender": "",
                "date_of_birth": "",
                "date_created": "",
                "slug": ""
            }
            return Response(final_data)
# </editor-fold>


class accountsClientUserSkillScoreDetailsAPIView(APIView):
    serializer_class = accountsClientUserSkillScoreInfoSerializer
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]
    pagination_class = None

    def get(self,request,slug):
        try:
            main_user = accountsUserSkillScoreModel.objects.get(slug=slug)
            serializer = accountsClientUserSkillScoreInfoSerializer(main_user)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response(f"somthing went wrong{e}")


class accountsClientUserAllReferalUsersGenericsView(generics.ListAPIView,generics.CreateAPIView):
    serializer_class = accountsUserAllReferalSerializers
    queryset = accountsUserReferalCodeModel.objects.all()
    permission_classes = (IsAuthenticated,)
    authenticate_class = [SessionAuthentication,BasicAuthentication,TokenAuthentication]

    pagination_class = LimitOffsetPagination

    search_fields = []
    filter_backends = (filters.SearchFilter,)

    def list(self,request,*args, **kwargs):
        serializer = self.get_serializer(self.paginate_queryset(self.filter_queryset(self.get_queryset().filter(owner=request.user))), many=True,
                                         context={"request": request})
        return self.get_paginated_response(serializer.data)


class accountsClientUserSkillScoreAPIView(generics.ListAPIView):
    serializer_class = accountsUserAllReferalSerializers
    queryset = accountsUserReferalCodeModel.objects.all()


    def get(self,request):
        user = request.data["user"]
        cricket_score = request.data["skill_score"]
        user_score = accountsUserSkillScoreModel.objects.get(owner__phone_number=user)
        user_score.cricket_score=cricket_score
        user_score.save()
        return Response("success")
