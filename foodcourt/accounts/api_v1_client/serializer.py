import datetime
import random
from django.forms.models import model_to_dict
from ..models import accountsUserLoginOtpModel,accountsUserProfileModel,accountsAdminUserCreationLoginOtpModel
from django.db.models import Q
from rest_framework import serializers, status
from django.contrib.auth import get_user_model
from ..utils import get_tokens_for_user
from django.utils.crypto import get_random_string
import string
from django.core.mail import send_mail
import json
from datetime import datetime
from srk_projects_core.twillo import send_message_otp


# <editor-fold desc="MAIN PROFILE LOGIN USER USER MODEL ALL DETAILS">
class accountsClientLoginUserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        exclude = ["password",]
# </editor-fold>


##PROFILE LOGIN USER  DETAILS
class accountsClientLoginUserProfileSerializer(serializers.ModelSerializer):
    user_profile = serializers.ReadOnlyField(source="user_profile.phone_number")

    class Meta:
        model = accountsUserProfileModel
        fields = "__all__"

##USER BY EMAIL SEARCH
class accountsClientUsersSearchSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField(read_only=True)

    def get_image(self,obj):
        try:
            image = obj.accountsUserProfileModel_user_profile.image.url
        except:
            image = ""
        return image

    class Meta:
        model = get_user_model()
        fields = ["email","id","phone_number","employee_id","image",]

class accountsUserOtpLoginSerializers(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        exclude=('password','last_login','date_created','groups','user_permissions')
        # fields = ["id","phone_number","employee_id","email","is_approved","is_active","is_staff","is_admin","is_supervisor","is_employee","is_store_manager","slug"]
        # fields = ["id","phone_number","employee_id","email","is_approved","is_active","is_staff","is_admin","is_supervisor","is_employee","is_store_manager","is_engineer","is_finance","is_head_office","is_main_owner","slug"]


class accountsUserProfileSerializers(serializers.ModelSerializer):
    user_profile = serializers.ReadOnlyField(source="user_profile.phone_number")
    class Meta:
        model = accountsUserProfileModel
        fields = "__all__"

##ALL USERS WITH PROFILES
class usersProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = "__all__"

class userModelGetSerializers(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ["id","phone_number","employee_id","email","slug",]

class accountsCommonUserSerializers(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="userProfileModel_user_profile.name")

    class Meta:
        model = get_user_model()
        fields =["phone_number","id","name"]


"""
    Create User 

"""


class userModelSerializers(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("email", "id", "phone_number", 'password')

"""
token generation and otp login 
"""

class UserCheckAndcreationSerializer(serializers.Serializer):
    phone = serializers.IntegerField(required=True)
    email = serializers.EmailField(required=False)
    name = serializers.CharField(max_length=200,required=True)
    referal_code = serializers.CharField(max_length=50,required=False)
    date_of_birth = serializers.DateField(required=True)

    def validate(self,data):
        phone = data.get("phone")
        email = data.get("email", None)
        name = data.get("name")
        referal_code = data.get("referal_code",None)

        birthday = data.get("date_of_birth")
        today_date = datetime.today().date()
        difference = today_date - birthday
        difference_in_years = (difference.days + difference.seconds / 86400) / 365.2425

        user_check = get_user_model().objects.filter(phone_number=phone)
        user_mail_check = get_user_model().objects.filter(email=email)
        if len(user_mail_check) == 0:
            pass
        else:
            raise serializers.ValidationError({"message": "A user with this Email already exists"})
        if len(user_check) == 0:
            pass
        else:
            raise serializers.ValidationError({"message":"A user with this Phone already exists"})

        if difference_in_years < 18:
            raise serializers.ValidationError({"message": "Minors Are Not Allowed To Play The Game"})
        else:
            pass
        if referal_code == None:
            try:
                user_creation = get_user_model().objects.create_employee(phone_number=phone,password=str(phone))
                # user_creation.name = name
                user_creation.email = email
                user_creation.save()

                try:
                    user_profile = accountsUserProfileModel.objects.create(user_profile=user_creation,
                                                                           name=name,
                                                                           date_of_birth=birthday,
                                                                           user_game_name=name+str(random.randint(1000, 9999)))
                except Exception as e:
                    user_creation.delete()
                    raise serializers.ValidationError({"message": f"unable to create profile {e}", "status": status.HTTP_400_BAD_REQUEST})
                try:
                    # user_name = name
                    splited_name = name.split()
                    code = splited_name[0].upper() + str(user_creation.id) + get_random_string(5,string.ascii_uppercase + string.digits)
                    user_referal_code = accountsUserReferalCodeModel.objects.create(owner=user_creation,referal_code=referal_code_generator(user_creation))
                except Exception as e:
                    user_creation.delete()
                    user_profile.delete()
                    raise serializers.ValidationError({"message": f"unable to create referal code {e}", "status": status.HTTP_400_BAD_REQUEST})
                try:
                    # print(email,3125243534324525)
                    user_email = accountsUserEmailUpdateModel.objects.create(owner=user_creation,email=email)
                except Exception as e:
                    user_creation.delete()
                    user_profile.delete()
                    user_referal_code.delete()
                    raise serializers.ValidationError({"message": f"unable to create email code {e}", "status": status.HTTP_400_BAD_REQUEST})
                try:
                    url = f"{base_url}accounts/api/v1/client/user-register/"

                    payload = json.dumps({
                        "email": email,
                        "name": name,
                        "phone_number": phone,
                        "password": str(phone)
                    })

                    headers = {
                        # 'Authorization': 'Basic MDow',
                        'Content-Type': 'application/json'
                    }

                    response = requests.request("POST", url, headers=headers, data=payload)
                    final_response = response.text
                    final_data = json.loads(final_response)
                except Exception as e:
                    user_creation.delete()
                    user_profile.delete()
                    user_referal_code.delete()
                    user_email.delete()
                    raise serializers.ValidationError({"message": f"unable to create account {e}","status":status.HTTP_400_BAD_REQUEST})
            except Exception as e:
                raise serializers.ValidationError({"message":f"unable to create account {e}","status":status.HTTP_400_BAD_REQUEST})
        else:
            code = accountsUserReferalCodeModel.objects.filter(referal_code=referal_code).last()
            if code:
                pass
            else:
                raise serializers.ValidationError({"message":"Please Enter A Valid Referal Code"})
            try:
                user_creation = get_user_model().objects.create_employee(phone_number=phone,password=str(phone))
                user_creation.email = email
                user_creation.referal_code = referal_code
                user_creation.save()
                code.no_of_times += 1
                code.save()
                code.users_used.add(user_creation)
                try:
                    user_profile = accountsUserProfileModel.objects.create(user_profile=user_creation,
                                                                           name=name,
                                                                           date_of_birth=birthday,
                                                                           user_game_name=name+str(random.randint(1000, 9999)))
                except:
                    user_creation.delete()
                    code.no_of_times -= 1
                    code.save()
                    code.users_used.remove(user_creation)
                    raise serializers.ValidationError(
                        {"message": "unable to create profile", "status": status.HTTP_400_BAD_REQUEST})
                try:
                    splited_name = name.split()
                    code = splited_name[0].upper() + str(user_creation.id) + get_random_string(5,string.ascii_uppercase + string.digits)
                    user_referal_code = accountsUserReferalCodeModel.objects.create(owner=user_creation,referal_code=referal_code_generator(user_creation))
                except:
                    user_creation.delete()
                    code.no_of_times -= 1
                    code.save()
                    code.users_used.remove(user_creation)
                    user_profile.delete()
                    raise serializers.ValidationError(
                        {"message": "unable to create referal code", "status": status.HTTP_400_BAD_REQUEST})
                try:
                    user_email = accountsUserEmailUpdateModel.objects.create(owner=user_creation, email=email)
                except Exception as e:
                    user_creation.delete()
                    code.no_of_times -= 1
                    code.save()
                    code.users_used.remove(user_creation)
                    user_profile.delete()
                    user_referal_code.delete()
                    raise serializers.ValidationError(
                        {"message": "unable to create email code", "status": status.HTTP_400_BAD_REQUEST})

                # cash_bonus = paymentUserContestParticipateModel.objects.create(owner=code.owner,transaction_id="createnewtransactionid",bonus_reduced=100,type="OFFER")
                # referal_wallet = code.owner.walletUserWModel_owner
                # referal_wallet.cash_bonus += 100
                # referal_wallet.save()
                try:
                    url = f"{base_url}accounts/api/v1/client/user-register/"

                    payload = json.dumps({
                        "email": email,
                        "name": name,
                        "phone_number": phone,
                        "password": str(phone)
                    })

                    headers = {
                        # 'Authorization': 'Basic MDow',
                        'Content-Type': 'application/json'
                    }

                    response = requests.request("POST", url, headers=headers, data=payload)
                    final_response = response.text
                    final_data = json.loads(final_response)
                    # code.users_used.add(user_creation)
                    # code.no_of_times += 1
                    # code.save()
                except Exception as e:
                    print(e)
                    user_creation.delete()
                    code.no_of_times -= 1
                    code.save()
                    code.users_used.remove(user_creation)
                    user_profile.delete()
                    user_referal_code.delete()
                    user_email.delete()
                    raise serializers.ValidationError(
                        {"message": "unable to create account", "status": status.HTTP_400_BAD_REQUEST})
            except Exception as e:
                print(e)
                raise serializers.ValidationError(
                    {"message": f"unable to create account {e}", "status": status.HTTP_400_BAD_REQUEST})
        return {
            'name': name,
            'phone':phone,
            'date_of_birth':birthday
        }

class userPhoneCheckSerializer(serializers.Serializer):
    phone = serializers.IntegerField(required=True)
    data = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        phone = data.get("phone", None)
        user = get_user_model().objects.filter(phone_number=phone)

        if user.count() == 0:
            raise serializers.ValidationError({"message": "A User with this Phone is not found.", 'status': status.HTTP_400_BAD_REQUEST})

        final_otp = random.randint(1000, 9999)
        try:
            try:
                send_message_otp(phone, final_otp)
            except:
                raise serializers.ValidationError({"message":"unable to send otp","status":status.HTTP_400_BAD_REQUEST})
            accountsUserLoginOtpModel.objects.create(owner=user.first(), otp=final_otp)
        except:
            raise serializers.ValidationError(
                'otp failed'
            )

        return {
            'phone':phone,
            'data':True
        }


class userEmailCheckSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    data = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        email = data.get("email", None)
        user = get_user_model().objects.filter(email=email)

        if user.count() == 0:
            pass
        else:
            raise serializers.ValidationError(
                    {"user": "A User with this Email is already found.", 'status': status.HTTP_400_BAD_REQUEST})

        final_otp = random.randint(1000, 9999)
        try:
            send_mail(
                'The Otp Is From Win11',
                f'The Otp To Login Is {final_otp}',
                'info@techarion.com',
                [email],
                fail_silently=False,
            )
            # send_message_otp(phone, final_otp)
            accountsUserEmailUpdateModel.objects.create(owner=user.first(),otp=final_otp,verified=False)
        except:
            raise serializers.ValidationError(
                'otp failed'
            )

        return {
                'email': email,
                'data': True
            }

    # def validate(self, data):
    #     phone = data.get("phone", None)
    #     user = get_user_model().objects.filter(phone_number=phone)
    #     if len(user) == 0:
    #         main_user = get_user_model().objects.create_employee(phone_number=phone,email="a@a.com")
    #         final_otp = random.randint(1000, 9999)
    #         try:
    #             send_message_otp(phone, final_otp)
    #             accountsUserLoginOtpModel.objects.create(owner=main_user, otp=final_otp)
    #         except:
    #             raise serializers.ValidationError('otp failed')
    #     else:
    #
    #         final_otp = random.randint(1000, 9999)
    #         try:
    #             send_message_otp(phone, final_otp)
    #             accountsUserLoginOtpModel.objects.create(owner=user.first(), otp=final_otp)
    #         except:
    #             raise serializers.ValidationError('otp failed')
    #     return {
    #         'phone':phone,
    #         'data':True
    #     }

"""
log in and token

"""

class UserLoginSerializer(serializers.Serializer):
    phone = serializers.IntegerField(required=True)
    otp = serializers.IntegerField(write_only=True,required=True)
    access = serializers.CharField(max_length=255, read_only=True)
    refresh = serializers.CharField(max_length=255, read_only=True)
    # cricket_refresh = serializers.CharField(max_length=255, read_only=True)
    # cricket_access =serializers.CharField(max_length=255, read_only=True)
    # name = serializers.CharField(max_length=75, read_only=True)
    # image = serializers.ImageField(read_only=True)

    def validate(self, data):
        phone = data.get("phone", None)
        otp = data.get("otp", None)
        user = get_user_model().objects.filter(phone_number=phone)
        if user:
            pass
        else:
            raise serializers.ValidationError({
                "message":'A user with this Phone is not found.'})
        user = user.first()
        if user.accountsUserLoginOtpModel_user.filter(active=True,otp=otp):
            pass
        else:
            raise serializers.ValidationError({"message":'Please enter a valid OTP'})
        # user = authenticate(phone=user.phone_number, password=user.password)
        if user is None:
            raise serializers.ValidationError(
                'A user with this email and password is not found.'
            )
        jwt_token = get_tokens_for_user(user)
        # print(phone,phone)
        # url = f"{base_url}accounts/api/v1/client/user-phone-password/"
        #
        # payload = json.dumps({
        #     "phone": phone,
        #     "password": str(phone)
        # })
        # headers = {
        #     'Content-Type': 'application/json'
        # }
        #
        # response = requests.request("POST", url, headers=headers, data=payload)
        # final_response = response.text
        # data = json.loads(final_response)
        # print(data)
        # refresh_token = data["refresh"]
        # if data
        return {
            # 'name':user.name,
            # 'email':user.email,
            'phone':user.phone_number,
            'access': jwt_token["access"],
            'refresh':jwt_token["refresh"],
            # 'cricket_refresh':data["refresh"],
            # 'cricket_access':data["access"],
        }


class UserEmailOtpLoginSerializer(serializers.Serializer):

    email = serializers.EmailField(required=True)
    otp = serializers.IntegerField(write_only=True,required=True)
    access = serializers.CharField(max_length=255, read_only=True)
    refresh = serializers.CharField(max_length=255, read_only=True)
    # name = serializers.CharField(max_length=75, read_only=True)
    # image = serializers.ImageField(read_only=True)

    def validate(self, data):
        email = data.get("email", None)
        otp = data.get("otp", None)
        user = get_user_model().objects.filter(email=email)
        if user:
            pass
        else:
            raise serializers.ValidationError({
                "message":'A user with this Email is not found.'})
        user = user.first()
        if user.accountsUserLoginOtpModel_user.filter(active=True,otp=otp):
            pass
        else:
            raise serializers.ValidationError({"message":'Please enter a valid OTP'})
        # user = authenticate(phone=user.phone_number, password=user.password)
        if user is None:
            raise serializers.ValidationError(
                'A user with this email and password is not found.'
            )
        jwt_token = get_tokens_for_user(user)
        return {
            # 'name':user.name,
            # 'email':user.email,
            'email':user.email,
            'access': jwt_token["access"],
            'refresh':jwt_token["refresh"],
        }

"""
login and token end
"""
"""
user enroll api
"""



class UserEnrollmentSerializer(serializers.Serializer):

    phone = serializers.IntegerField(required=True)
    check = serializers.BooleanField(required=False)

    def validate(self, data):
        phone = data.get("phone", None)
        user = get_user_model().objects.filter(phone_number=phone)
        final_otp = random.randint(1000, 9999)
        if user:
            data_not_found = False
            try:
                user_data = user.first().userProfileModel_user_profile
                data_not_found = True
            except:
                try:
                    send_message_otp(phone,final_otp)
                    accountsUserLoginOtpModel.objects.create(owner=user.first(),otp = final_otp)
                except:
                    # print("otp failed")
                    return {
                    'phone': phone,"check":False
                }
            if data_not_found:
                return {'phone':phone,"check":False}
        else:
            try:
                send_message_otp(phone, final_otp)
                user_data = get_user_model().objects.create_initial_user_login(phone_number=phone)
                accountsUserLoginOtpModel.objects.create(owner=user_data, otp=final_otp)
            except:
                # print("otp failed")
                return {'phone': phone, "check": False}

            return {
                'phone': phone,"check":True
            }


class accountsClientGetUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = "__all__"


"""
all user details start
# """

class accountsEmailLoginSerializer(serializers.Serializer):
    # phone = serializers.IntegerField(required=True)
    # otp = serializers.IntegerField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(max_length=100,required=True)
    access = serializers.CharField(max_length=255, read_only=True)
    refresh = serializers.CharField(max_length=255, read_only=True)
    name = serializers.CharField(max_length=75, read_only=True)
    image = serializers.ImageField(read_only=True)

    def validate(self, data):
        main_email = data.get("email", None)
        main_password = data.get("password", None)
        user = get_user_model().objects.filter(email=main_email)
        if user:
            pass
        else:
            raise serializers.ValidationError({"user": "A user with this email doesn't exists", 'status': status.HTTP_400_BAD_REQUEST})
        main_user = user.first()
        # user_validation = authenticate(email=main_email,password=main_password)
        # if user_validation:
        #     pass
        # else:
        #     raise serializers.ValidationError(
        #         'Please enter a valid Password'
        #     )
        if main_user.check_password(main_password):
            pass
        else:
            raise serializers.ValidationError(
                {"user": "A user with this email and password is not found.", 'status': status.HTTP_400_BAD_REQUEST})


        jwt_token = get_tokens_for_user(main_user)
        return {
            # 'name':user.get_employees_name(),
            # 'image':user.get_user_image(),
            'email': main_user.email,
            'password':main_user.email,
            'access': jwt_token["access"],
            'refresh': jwt_token["refresh"],
        }

    class Meta:
        fields = "__all__"


# class UserCheckAndcreationWithEmailSerializer(serializers.Serializer):
#     phone_number = serializers.IntegerField(required=False)
#     email = serializers.EmailField(required=True)
#     name = serializers.CharField(max_length=200,required=True)
#     referal_code = serializers.CharField(max_length=50,required=False)
#     access = serializers.CharField(max_length=255, read_only=True)
#     refresh = serializers.CharField(max_length=255, read_only=True)
#
#
#     def validate(self,data):
#         phone = data.get("phone_number")
#         email = data.get("email")
#         name = data.get("name")
#         referal_code = data.get("referal_code")
#         if referal_code == None and phone == None:
#             try:
#                 user_creation = get_user_model().objects.create_employee(email=email)
#                 try:
#                     user_profile = accountsUserProfileModel.objects.create(user_profile=user_creation,name=name)
#                 except:
#                     user_creation.delete()
#                     raise serializers.ValidationError("user profile not created")
#                 try:
#                     splited_name = name.split()
#                     code = splited_name[0].upper() + str(user_creation.id) + get_random_string(5,string.ascii_uppercase + string.digits)
#                     user_referal_code = accountsUserReferalCodeModel.objects.create(owner=user_creation,referal_code=code)
#                 except:
#                     user_creation.delete()
#                     user_profile.delete()
#                     raise serializers.ValidationError("User referal code not created")
#                 # try:
#                 #     # bitgo_wallet = bitgoWalletCreationRequestModel.objects.create(user=user_creation,
#                 #     #                                                wallet_lable=name,
#                 #     #                                                wallet_password=("TIAR" + str(random.randint(1000,9999))),
#                 #     #                                                wallet_coin="gteth",
#                 #     #                                                status="PENDING")
#                 #     # wallet_creation_bitgo()
#                 #     # wallet_creation()
#                 #     userCreateVirtualWallet(user_creation,name)
#                 # except:
#                 #     user_referal_code.delete()
#                 #     user_creation.delete()
#                 #     user_profile.delete()
#                 #     raise serializers.ValidationError("Bitgo wallet not created")
#                 # wallet_creation_bitgo()
#                 # wallet_creation()
#             except Exception as e:
#                 raise serializers.ValidationError(f"{e}")
#         elif phone == None:
#             # code = accountsUserReferalCodeModel.objects.filter(referal_code=referal_code).last()
#             # if code:
#             #     code.no_of_times += 1
#             #     code.save()
#             # else:
#             #     raise serializers.ValidationError({"message":"Please Enter A Valid Referal Code"})
#             try:
#                 user_creation = get_user_model().objects.create_employee(email=email)
#                 user_creation.referal_code = referal_code
#                 user_creation.save()
#
#                 code = accountsUserReferalCodeModel.objects.filter(referal_code=referal_code).last()
#                 if code:
#                     code.no_of_times += 1
#                     code.save()
#                 else:
#                     pass
#                 try:
#                     user_profile = accountsUserProfileModel.objects.create(user_profile=user_creation,name=name)
#                 except:
#                     user_creation.delete()
#                     raise serializers.ValidationError("user profile not created")
#                 code.users_used.add(user_creation)
#                 try:
#
#                     user_referal_code = accountsUserReferalCodeModel.objects.create(owner=user_creation,referal_code=get_random_string(7, string.ascii_uppercase+string.digits))
#                 except:
#                     user_creation.delete()
#                     user_profile.delete()
#                     raise serializers.ValidationError("User referal code not created")
#                 # try:
#                 #     # bitgo_wallet = bitgoWalletCreationRequestModel.objects.create(user=user_creation,
#                 #     #                                                wallet_lable=name,
#                 #     #                                                wallet_password=("TIAR" + str(random.randint(1000,9999))),
#                 #     #                                                wallet_coin="gteth",
#                 #     #                                                status="PENDING")
#                 #     # wallet_creation_bitgo()
#                 #     # wallet_creation()
#                 #     userCreateVirtualWallet(user_creation, name)
#                 # except:
#                 #     user_referal_code.delete()
#                 #     user_creation.delete()
#                 #     user_profile.delete()
#                 #     raise serializers.ValidationError("Bitgo wallet not created")
#
#             except Exception as e:
#                 raise serializers.ValidationError(f"{e}")
#         elif referal_code == None:
#             try:
#                 user_creation = get_user_model().objects.create_employee(email=email)
#                 user_creation.phone_number = phone
#                 user_creation.save()
#                 try:
#                     user_profile = accountsUserProfileModel.objects.create(user_profile=user_creation,name=name)
#                 except:
#                     user_creation.delete()
#                     raise serializers.ValidationError("user profile not created")
#                 try:
#                     user_referal_code = accountsUserReferalCodeModel.objects.create(owner=user_creation,referal_code=get_random_string(7, string.ascii_uppercase+string.digits))
#                 except:
#                     user_creation.delete()
#                     user_profile.delete()
#                     raise serializers.ValidationError("User referal code not created")
#                 # try:
#                     # bitgo_wallet = bitgoWalletCreationRequestModel.objects.create(user=user_creation,
#                     #                                                wallet_lable=name,
#                     #                                                wallet_password=("TIAR" + str(random.randint(1000,9999))),
#                     #                                                wallet_coin="gteth",
#                     #                                                status="PENDING")
#                     # wallet_creation_bitgo()
#                     # wallet_creation()
#                     # userCreateVirtualWallet(user_creation, name)
#                 # except:
#                 #     user_referal_code.delete()
#                 #     user_creation.delete()
#                 #     user_profile.delete()
#                 #     raise serializers.ValidationError("bitgo wallet not created")
#
#             except Exception as e:
#                 raise serializers.ValidationError(f"{e}")
#         elif referal_code != None and phone != None:
#             code = accountsUserReferalCodeModel.objects.filter(referal_code=referal_code).last()
#             if code:
#                 code.no_of_times += 1
#                 code.save()
#             else:
#                 raise serializers.ValidationError({"message": "Please Enter A Valid Referal Code"})
#             try:
#                 user_creation = get_user_model().objects.create_employee(email=email)
#                 user_creation.phone_number = phone
#                 user_creation.referal_code = referal_code
#                 user_creation.save()
#                 try:
#                     user_profile = accountsUserProfileModel.objects.create(user_profile=user_creation, name=name)
#                 except:
#                     user_creation.delete()
#                     raise serializers.ValidationError("user profile not created")
#                 code.users_used.add(user_creation)
#                 # try:
#                 #     user_referal_code = accountsUserReferalCodeModel.objects.create(owner=user_creation,
#                 #                                                                     referal_code=get_random_string(7,
#                 #                                                                                                    string.ascii_uppercase + string.digits))
#                 # except:
#                 #     user_creation.delete()
#                 #     user_profile.delete()
#                 #     raise serializers.ValidationError("User referal code not created")
#                 # try:
#                 #     # bitgo_wallet = bitgoWalletCreationRequestModel.objects.create(user=user_creation,
#                 #     #                                                wallet_lable=name,
#                 #     #                                                wallet_password=("TIAR" + str(random.randint(1000,9999))),
#                 #     #                                                wallet_coin="gteth",
#                 #     #                                                status="PENDING")
#                 #     # wallet_creation_bitgo()
#                 #     # wallet_creation()
#                 #     userCreateVirtualWallet(user_creation, name)
#                 # except:
#                 #     user_referal_code.delete()
#                 #     user_creation.delete()
#                 #     user_profile.delete()
#                 #     raise serializers.ValidationError("Bitgo wallet not created")
#
#             except Exception as e:
#                 raise serializers.ValidationError(f"{e}")
#         jwt_token = get_tokens_for_user(user_creation)
#
#         return {
#             'name': name,
#             'email':email,
#             'access': jwt_token["access"],
#             'refresh': jwt_token["refresh"]
#         }

class accountsClientUpdateUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = "__all__"

class accountsClientUpdateUserProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = ["image"]

class accountsClientUserDetailsSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField(read_only=True)

    def get_user_profile(self,obj):
        try:
            user_profile = usersProfileSerializer(obj.accountsUserProfileModel_user_profile).data
        except:
            user_profile = {}
        return user_profile
    class Meta:
        model = get_user_model()
        exclude = ["password","last_login","is_superuser","is_approved","is_active","is_staff","is_admin","is_employee"]


class accountsClientUserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = ["name","gender","date_of_birth","image"]

    def validate(self,data):
        today_date = datetime.today().date()
        birthday = data["date_of_birth"]
        difference = today_date - birthday
        difference_in_years = (difference.days + difference.seconds / 86400) / 365.2425
        if difference_in_years < 18:
            raise serializers.ValidationError({"message":"Minors Are Not Allowed To Play The Game"})
        else:
            pass
        return data

class accountsClientUserProfileUpdateImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = ["image"]


# class userPhoneUpdateSendOtpSerializer(serializers.Serializer):
#     phone = serializers.IntegerField(required=True)
#     data = serializers.CharField(max_length=255, read_only=True)
#     user = serializers.IntegerField(required=False)
#
#     def validate(self, data):
#         user = data.get("user")
#         phone = data.get("phone", None)
#         phone_number_check = get_user_model().objects.filter(phone_number=phone)
#         if len(phone_number_check) == 0:
#             pass
#         else:
#             raise serializers.ValidationError("User with this number already exists")
#         final_otp = random.randint(1000, 9999)
#         final_user = get_user_model().objects.filter(phone_number=user).last()
#         try:
#             send_message_otp(phone, final_otp)
#             accountsUserPhoneUpdateModel.objects.create(owner=final_user,phone_number=phone, otp=final_otp)
#         except Exception as e:
#             print(e)
#             raise serializers.ValidationError(f"Somthing went wrong {e}")
#
#         return {
#             'phone':phone,
#             'data':True
#         }


# class accountsClientUserPhoneUpdateSerializer(serializers.Serializer):
#     phone = serializers.IntegerField(required=True)
#     data = serializers.CharField(max_length=255, read_only=True)
#     user = serializers.IntegerField(required=False)
#     otp = serializers.IntegerField(required=True,write_only=True)
#     class Meta:
#         fields = "__all__"
#
#     def validate(self, data):
#         user = data.get("user")
#         otp = data.get("otp")
#         phone = data.get("phone")
#         final_user = get_user_model().objects.filter(phone_number=user).last()
#         instance = accountsUserPhoneUpdateModel.objects.filter(owner=final_user,phone_number=phone, otp=otp,active=True).last()
#         if instance:
#             final_user.phone_number=phone
#             final_user.save()
#             return {
#                 'phone': phone,
#                 'data': True
#             }
#         else:
#             return {
#                 'phone': phone,
#                 'data': False
#             }


# class accountsClientEmailUpdateOtpSerializer(serializers.Serializer):
#     email = serializers.EmailField(required=True,write_only=True)
#     data = serializers.CharField(max_length=255, read_only=True)
#     user = serializers.IntegerField(required=False)
#
#     def validate(self, data):
#         email = data.get("email", None)
#         user = data.get("user")
#         final_user = get_user_model().objects.filter(phone_number=user).last()
#         user_check = get_user_model().objects.filter(email=email)
#
#         if len(user_check)>1:
#             raise serializers.ValidationError("A user with this Email already exists")
#         else:
#             pass
#         final_otp = random.randint(1000, 9999)
#         try:
#             send_mail(
#                 'OTP verification - WIN-11 APP',
#                 f'Dear User,\n\n It looks like you are trying to Change Your Email Id in WIN-11 APP.\n\n Your One Time Password (OTP) is {final_otp}\n\n\n Team WIN-11',
#                 'info@techarion.com',
#                 [email],
#                 fail_silently=False,
#             )
#             # send_message_otp(phone, final_otp)final_otp
#             user_email = accountsUserEmailUpdateModel.objects.filter(owner=final_user).last()
#
#             if user_email:
#                 user_email.email = email
#                 user_email.otp = final_otp
#                 user_email.save()
#             else:
#                 user_email = accountsUserEmailUpdateModel.objects.create(owner=final_user,email=email,otp=final_otp)
#
#         except Exception as e:
#             raise serializers.ValidationError(f"Somthing went wrong {e}")
#
#         return {
#                 'email': email,
#                 'data': True
#             }




# class accountsClientGetUserAddressSerializer(serializers.ModelSerializer):
#     owner = serializers.ReadOnlyField(source="owner__phone_number")
#     state_details=serializers.SerializerMethodField(read_only=True)
#     city_details=serializers.SerializerMethodField(read_only=True)
#     country_details=serializers.SerializerMethodField(read_only=True)
#
#     def get_state_details(self, obj):
#         try:
#             state = obj.state.states
#         except:
#             state = ""
#         return state
#
#     def get_city_details(self, obj):
#         try:
#             city = obj.city.city
#         except:
#             city = ""
#         return city
#
#     def get_country_details(self, obj):
#         try:
#             country = obj.country.country
#         except:
#             country = ""
#         return country
#
#
#     class Meta:
#         model = accountsUserAddressModel
#         fields = "__all__"



# class accountsClientUserInfoSerializer(serializers.ModelSerializer):
#     user_profile = serializers.SerializerMethodField(read_only=True)
#     address = serializers.SerializerMethodField(read_only=True)
#     #
#     def get_address(self,obj):
#         address = accountsUserAddressModel.objects.filter(owner=obj).last()
#         serializer = accountsClientGetUserAddressSerializer(address).data
#         if address:
#             return serializer
#         else:
#             serializer = {}
#             return serializer
#
#     def get_user_profile(self,obj):
#         try:
#             user_profile = accountsUserProfileModel.objects.filter(user_profile=obj).last()
#             serializer = accountsClientLoginUserProfileSerializer(user_profile).data
#         except:
#             serializer = {}
#         return serializer
#     class Meta:
#         model = get_user_model()
#         exclude = ["password","user_permissions","is_employee","is_admin","is_staff","is_active","is_approved"]



# <editor-fold desc="User Profile Details with skill score">
# class accountsClientUserProfileInfoSerializer(serializers.ModelSerializer):
#     skill_score = serializers.SerializerMethodField(read_only=True)
#     user_profile = serializers.SerializerMethodField(read_only=True)
#
#     def get_skill_score(self,obj):
#         try:
#             skill_score = obj.user_profile.accountsUserSkillScoreModel_owner
#             final_score = model_to_dict(skill_score)
#         except:
#             final_score = {}
#         return final_score
#
#     def get_user_profile(self,obj):
#         user_playong_since = obj.user_profile.date_created
#         return user_playong_since
#     class Meta:
#         model = accountsUserProfileModel
#         fields = "__all__"
# </editor-fold>

