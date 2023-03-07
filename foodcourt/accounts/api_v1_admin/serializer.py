import json
import random
import re
import requests
import string
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.utils.crypto import get_random_string
from django.utils.datetime_safe import datetime
from rest_framework import serializers, status

from accounts.models import accountsUserLoginOtpModel
from accounts.signals import user_roles
from attendance.models import attendanceUserAttendanceImageModel, attendanceUserAttendanceLocationsModel, \
    attendanceLocationsModel
from coreUtils.models import coreUtilsCountryModel, coreUtilsStatesModel, coreUtilsCityModel
from projects.models import projectsPAttendanceUsersModel, projectsPModel, projectsRoadModel
from srk_projects_core.twillo import send_message_otp
from ..models import accountsUserProfileModel, accountsUserAddressModel
from ..utils import get_tokens_for_user


# <editor-fold desc="Serializer For User Creation">
class accountsAdminTechanicianProfileDetailSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.CharField(required=True)

    class Meta:
        model = accountsUserProfileModel
        fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'id_Proof', 'image']


class accountsTechanicianAddressCreateSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField()
    city = serializers.CharField(write_only=True, required=True)
    state = serializers.CharField(write_only=True, required=True)
    country = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = accountsUserAddressModel
        fields = ['owner','address', 'pincode', 'address_proof', "city", "state", "country"]

    def create(self, validated_data):
        city = validated_data.pop('city', None)
        state = validated_data.pop('state', None)
        country = validated_data.pop('country', None)
        try:
            instance_country = coreUtilsCountryModel.objects.get(country__iexact=country)
        except:
            instance_country = coreUtilsCountryModel.objects.create(country=country)

        try:
            instance_state = coreUtilsStatesModel.objects.get(states__iexact=state)
        except:
            instance_state = coreUtilsStatesModel.objects.create(states=state, country_state=instance_country)

        try:
            instance_city = coreUtilsCityModel.objects.get(city__iexact=city)
        except:
            instance_city = coreUtilsCityModel.objects.create(city=city,state_city=instance_state)

        instance = accountsUserAddressModel.objects.create(
            city=instance_city, state=instance_state, country=instance_country, **validated_data)
        return instance


class accountsAdminSupervisorRegistrationSerializer(serializers.ModelSerializer):
    profile = accountsAdminTechanicianProfileDetailSerializer(write_only=True)
    address = accountsTechanicianAddressCreateSerializer(write_only=True)
    phone_number = serializers.IntegerField(required=True, write_only=True)

    def validate(self, data):
        if get_user_model().objects.filter(phone_number=data["phone_number"]).exists():
            raise serializers.ValidationError(
                {"message": "A user with this Phone_number already exists", 'status': status.HTTP_400_BAD_REQUEST})
        return data

    class Meta:
        model = get_user_model()
        fields = ["phone_number", "profile", "address", ]

    def create(self, validated_data):
        profile = validated_data.get('profile', None)
        address = validated_data.get('address', None)
        phone = validated_data.pop("phone_number")

        try:
            user = get_user_model().objects.create_supervisor(phone_number=phone, password=str(phone))
            try:
                profile_instance = accountsUserProfileModel.objects.create(owner=user, **profile)
            except:
                user.delete()
                raise serializers.ValidationError({"Something wrong with User profile"})

            try:
                serializer = accountsTechanicianAddressCreateSerializer(data=address)
                if serializer.is_valid():
                    serializer.save(owner=user)
            except:
                user.delete()
                profile_instance.delete()
                raise serializers.ValidationError({"Something wrong with address"})

        except:
            raise serializers.ValidationError({f"Something wrong with user creation"})

        return user
# </editor-fold>

# <editor-fold desc="Serializer For get User Basic">
class accountsAdminUserProfileDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = ['name', 'age', 'image']


class accountsAdminUserGetAllSerializer(serializers.ModelSerializer):
    profile = accountsAdminUserProfileDetailSerializer(source="accountsUserProfileModel_owner", read_only=True)
    role = serializers.SerializerMethodField(read_only=True)

    def get_role(self, obj):
        user = user_roles(obj)
        return user

    class Meta:
        model = get_user_model()
        fields = ['id', 'employee_id', 'role', 'is_active', 'profile', 'slug']
# </editor-fold>


# <editor-fold desc="Serializer for Get LogIn User Details">
class accountsAdminUserProfileGetDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)

    class Meta:
        model = accountsUserProfileModel
        fields = ['name', 'age', 'image']


class accountsAdminUserGetDetailsSerializer(serializers.ModelSerializer):
    profile = accountsAdminUserProfileGetDetailSerializer(source="accountsUserProfileModel_owner", read_only=True)

    class Meta:
        model = get_user_model()
        exclude = ['password', 'groups', 'user_permissions', 'date_created']
# </editor-fold>


# <editor-fold desc="Serializer For User LogIn">
class accountsAdminUserLoginSerializer(serializers.Serializer):
    employee_id = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(max_length=100, required=True, write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, data):
        main_employee_id = data.get("employee_id")
        main_password = data.get("password")
        user = get_user_model().objects.filter(employee_id=main_employee_id)
        if not user.exists():
            raise serializers.ValidationError(
                {"message": "User doesn't exists", 'status': status.HTTP_400_BAD_REQUEST})
        main_user = user.first()

        if not main_user.check_password(main_password):
            raise serializers.ValidationError(
                {"message": "Password is Incorrect try again",'status': status.HTTP_400_BAD_REQUEST})
        jwt_token = get_tokens_for_user(main_user)
        return {
            'access': jwt_token["access"],
            'refresh': jwt_token["refresh"],
        }

    class Meta:
        fields = "__all__"
# </editor-fold>


# <editor-fold desc="Serializer for get User Details">
class accountsAdminUserAddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserAddressModel
        fields = ['address', 'pincode', 'user_city', "user_state", "user_country", "slug"]


class accountsAdminUserAboutProfileDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = ['name', 'age', 'image']


class accountsAdminUserAboutGetAllSerializer(serializers.ModelSerializer):
    profile = accountsAdminUserAboutProfileDetailSerializer(source="accountsUserProfileModel_owner", read_only=True)
    address = accountsAdminUserAddressDetailSerializer(source="accountsUserAddressModel_owner", read_only=True)

    class Meta:
        model = get_user_model()
        exclude = ["password", "user_permissions", "groups"]
# </editor-fold>


# <editor-fold desc="PERMISSIONS UPDATE">
class accountsAdminUserPermissionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['is_employee', 'is_supervisor', 'is_store_manager', 'is_gaurage_manager', 'slug']


# </editor-fold>

# <editor-fold desc="NEW SUPERVISOR">
class accountsAdminSupervisorProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = ['first_name', 'last_name']


# class accountsAdminSupervisorRegistrationSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(
#         required=True,
#         validators=[UniqueValidator(queryset=get_user_model().objects.all())]
#     )
#
#     password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
#     confirm_password2 = serializers.CharField(write_only=True, required=True)
#     profile = accountsAdminSupervisorProfileCreateSerializer(write_only=True)
#
#     class Meta:
#         model = get_user_model()
#         fields = ('phone_number', 'password', 'confirm_password2', 'email', 'profile')
#
#     def validate(self, data):
#         if data['password'] != data['confirm_password2']:
#             raise serializers.ValidationError({"password": "Password fields didn't match."})
#
#         if len(str(data.get('phone_number'))) < 10:
#             raise serializers.ValidationError(
#                 {"message": "Phone Number Must be 10 digits", 'status': status.HTTP_400_BAD_REQUEST})
#         elif len(str(data.get('phone_number'))) > 10:
#             raise serializers.ValidationError({"message": "Your Enter Phone Number Is More than 10 digits",
#                                                'status': status.HTTP_400_BAD_REQUEST})
#
#         return data
#
#     def create(self, validated_data):
#         profile = validated_data.get('profile')
#
#         user = get_user_model().objects.create_supervisor(
#             email=validated_data.get('email'),
#             phone_number=validated_data.get('phone_number'),
#
#         )
#         user.set_password(validated_data['password'])
#         user.save()
#         if user:
#             try:
#                 profile = accountsUserProfileModel.objects.get(owner=user)
#             except:
#                 profile = accountsUserProfileModel.objects.create(owner=user, first_name=profile.get('first_name'),
#                                                                   last_name=profile.get('last_name'))
#                 print(profile)
#
#             return user
# # </editor-fold>


# <editor-fold desc="User With Profile Serializer">
class accountsAdminUserProfileModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = "__all__"


class userModelAdminGetSerializers(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField(read_only=True)
    def get_user_profile(self, obj):
        try:
            user_profile = accountsAdminUserProfileModelSerializer(obj.accountsUserProfileModel_owner).data
        except:
            user_profile = {}
        return user_profile

    class Meta:
        model = get_user_model()
        exclude = ["password"]



# </editor-fold>

# # <editor-fold desc="Get User Address with slug">
# class accountsAdminGetUserAddressSerializer(serializers.ModelSerializer):
#     state = serializers.SerializerMethodField(read_only=True)
#     city = serializers.SerializerMethodField(read_only=True)
#     country = serializers.SerializerMethodField(read_only=True)
#
#     def get_state(self,obj):
#         try:
#             state = obj.state.states
#         except:
#             state = ""
#         return state
#
#     def get_city(self,obj):
#         try:
#             city = obj.city.city
#         except:
#             city = ""
#         return city
#
#     def get_country(self,obj):
#         try:
#             country = obj.country.country
#         except:
#             country = ""
#         return country
#     class Meta:
#         model = accountsUserAddressModel
#         fields = "__all__"
# # </editor-fold>

# # <editor-fold desc="Post User Address with slug">
# class accountsAdminUserAddressSerializer(serializers.ModelSerializer):
#     owner = serializers.ReadOnlyField(source="owner.phone_number")
#     class Meta:
#         model = accountsUserAddressModel
#         fields = "__all__"
# # </editor-fold>


# class accountsCricketContestAdminContestsModel(serializers.ModelSerializer):
#     class Meta:
#         model = cricketContestContestsModel
#         fields = "__all__"
#
#
# class accountsAdminCricketContestContestUserTeamsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = cricketContestContestUserTeamsModel
#         fields = "__all__"
#
#
# class accountsCricketContestAdminUserContestParticipationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = cricketContestUserContestParticipationModel
#         # fields = "__all__"
#         exclude = ["user"]
#         depth = 2


# class accountsAdminUsersPermissionsSerializers(serializers.ModelSerializer):
#     class Meta:
#         model = get_user_model()
#         exclude = ["password","last_login",]
#
#
# class accountsAdminUserProfileAttendanceSerializers(serializers.ModelSerializer):
#     owner_details = serializers.SerializerMethodField(read_only=True)
#     attendance_details = serializers.SerializerMethodField(read_only=True)
#
#     def get_attendance_details(self,obj):
#         attendance_details = {}
#         today = datetime.today().date()
#         one_week_ago = datetime.today() - timedelta(days=7)
#         one_month_ago = datetime.today() - timedelta(days=30)
#         attendance = obj.attendanceUserAttendanceMainModel_owner.filter(created_at__gte=one_month_ago,created_at__lte=today,approved="APPROVED")
#         attendance_week = obj.attendanceUserAttendanceMainModel_owner.filter(created_at__gte=one_week_ago,
#                                                                         created_at__lte=today,approved="APPROVED")
#         try:
#             locations_name = []
#             attendance_today = obj.attendanceUserAttendanceMainModel_owner.filter(created_at__contains=today)
#             if len(attendance_today) == 0:
#                 attendance_details["today_location"] = "ABSENT"
#                 attendance_details["today_attendance_time"] = "ABSENT"
#             for attendance_data in attendance_today:
#                 attendance_details["today_location"] = attendance_data.ref_location.title
#                 attendance_details["today_attendance_time"] = attendance_data.attendance_time
#         except:
#             raise serializers.ValidationError('Error while fetching todays attendance details')
#         attendance_details["monthly_presents"] = len(attendance)
#         # attendance_details["weekly_details"] = attendance_week.values()
#         attendance_details["weekly_presents"] = len(attendance_week)
#         return attendance_details
#
#     def get_owner_details(self,obj):
#         designations = []
#         if obj.is_superuser:
#             designations.append("superuser")
#         if obj.is_staff:
#             designations.append("staff")
#         if obj.is_admin:
#             designations.append("admin")
#         if obj.is_supervisor:
#             designations.append("supervisor")
#         if obj.is_employee:
#             designations.append("employee")
#         if obj.is_store_manager:
#             designations.append("store_manager")
#         if obj.is_engineer:
#             designations.append("engineer")
#         if obj.is_finance:
#             designations.append("finance")
#         if obj.is_head_office:
#             designations.append("head_office")
#         if obj.is_main_owner:
#             designations.append("main_owner")
#
#         owner_details = {}
#         owner_projects = projectsPAttendanceUsersModel.objects.filter(owner=obj)
#         try:
#             owner_profile = obj.accountsUserProfileModel_owner
#             owner_details["name"] = owner_profile.name
#             try:
#                 owner_details["image"] = owner_profile.image.url
#             except:
#                 owner_details["image"] = ""
#             owner_details["designation"] = designations
#             owner_details["owner_profile_slug"] = owner_profile.slug
#             owner_details["projects"] = owner_projects.values("project__title")
#         except:
#             owner_details = {"name":"","image":"","designation":designations,"owner_profile_slug":"owner_profile_slug","projects":[]}
#         return owner_details
#
#     class Meta:
#         model = get_user_model()
#         exclude = ["password",]
#
#
# class accountsAdminLoginOtpSerializers(serializers.Serializer):
#     phone = serializers.IntegerField(write_only=True,max_value=100000000000000)
#     active = serializers.BooleanField(write_only=True, required=False)
#
#     def validate(self, data, AdminUserCreationLoginOtp=None):
#         phone = data.get("phone", None)
#         user = get_user_model().objects.filter(phone_number=phone)
#         if len(user) == 0:
#             final_otp = random.randint(1000, 9999)
#             send_message_otp(phone,final_otp)
#             accountsAdminUserCreationLoginOtpModel.objects.create(phone_number=phone, otp=final_otp, active=True)
#             return {
#                 'phone': phone,
#                 'active': True
#             }
#         else:
#             raise serializers.ValidationError('User with this number already exist.')
#
#     class Meta:
#         fields = ["phone","active",]
#
#
# class accountsAdminUserMainDataSerializers(serializers.ModelSerializer):
#
#     class Meta:
#         model = get_user_model()
#         fields = ["phone_number","email",]
#
# class accountsAdminSupervisorUsersSerializers(serializers.ModelSerializer):
#     owner = serializers.ReadOnlyField(source="owner__phone_number")
#
#     class Meta:
#         model = attendanceUserAttendanceInChargeModel
#         fields = "__all__"
#
#
# class accountsAdminSupervisorLocationsSerializers(serializers.ModelSerializer):
#     owner = serializers.ReadOnlyField(source="owner__phone_number")
#     class Meta:
#         model = attendanceUserAttendanceLocationsModel
#         fields = "__all__"
#
# class accountsAdminUserAttendanceImageSerializer(serializers.ModelSerializer):
#     owner = serializers.ReadOnlyField(source="owner__phone_number")
#
#     class Meta:
#         model = attendanceUserAttendanceImageModel
#         fields = "__all__"
#
#
# ##CREATING SUPERVISOR
# class accountsAdminSupervisorCreationSerializers(serializers.ModelSerializer):
#     attendance_image = accountsAdminUserAttendanceImageSerializer(required=True,write_only=True)
#     user_profile =accountsAdminUserMainDataSerializers(required=True,write_only=True)
#     assigned_users = accountsAdminSupervisorUsersSerializers(write_only=True,required=False)
#     project = serializers.IntegerField(required=True,write_only=True)
#     location = accountsAdminSupervisorLocationsSerializers(required=True,write_only=True)
#     otp = serializers.IntegerField(required=True,write_only=True)
#
#     class Meta:
#         model = accountsUserProfileModel
#         fields = "__all__"
#
#     def create(self, validated_data):
#         initial_data = validated_data
#         try:
#             assigned_users = validated_data.pop("assigned_users")
#         except:
#             pass
#         user_profile = validated_data.pop("user_profile")
#         project = validated_data.pop("project")
#         location_data = validated_data.pop("location")
#         otp = validated_data.pop("otp")
#         user_att_image = validated_data.pop("attendance_image")
#
#         final_verification = accountsAdminUserCreationLoginOtpModel.objects.filter(phone_number=user_profile["phone_number"], otp=otp,active=True)
#         if final_verification:
#             try:
#                 owner = get_user_model().objects.create_supervisor(**user_profile)
#                 try:
#                     user_sub_profile = accountsUserProfileModel.objects.create(user_profile=owner,**validated_data)
#                 except Exception as e:
#                     owner.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=owner,**user_att_image)
#                 except Exception as e:
#                     owner.delete()
#                     user_sub_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     if len(assigned_users["assigned_users"]) != 0:
#                         try:
#                             main_assigned_users = attendanceUserAttendanceInChargeModel.objects.create(owner=owner)
#                             main_assigned_users.assigned_users.set(assigned_users["assigned_users"])
#                             main_assigned_users.save()
#                         except:
#                             owner.delete()
#                             user_sub_profile.delete()
#                             user_attendance_image.delete()
#                             raise serializers.ValidationError({f"something wrong with assigning users to supervisor"})
#                 except:
#                     pass
#                 try:
#                     assigning_project = projectsPAttendanceUsersModel.objects.get(project__id=project)
#                     assigning_project.owner.add(owner)
#                     assigning_project.save()
#                 except:
#                     try:
#                         exsisting_project = projectsPModel.objects.get(id=project)
#                         main_project = projectsPAttendanceUsersModel.objects.create(project=exsisting_project)
#                         main_project.owner.add(owner)
#                         main_project.save()
#                     except:
#                         try:
#                             main_assigned_users.delete()
#                         except:
#                             pass
#                         owner.delete()
#                         user_sub_profile.delete()
#                         user_attendance_image.delete()
#                         raise serializers.ValidationError({"something wrong with assigning users to Project"})
#
#                 try:
#                     supervisor_location = attendanceUserAttendanceLocationsModel.objects.create(location=location_data["location"],owner=owner)
#                 except:
#                     try:
#                         main_project.delete()
#                     except:
#                         pass
#                     try:
#                         main_assigned_users.delete()
#                     except:
#                         pass
#                     owner.delete()
#                     user_sub_profile.delete()
#                     user_attendance_image.delete()
#                     raise serializers.ValidationError({"something wrong with assigning users to Location"})
#
#             except Exception as e:
#                 raise serializers.ValidationError({f"something wrong with user creation ==> {e}"})
#             return initial_data
#         else:
#             raise serializers.ValidationError({"otp": "OTP is not valid"})
#
#
# ##CREATING MANAGER
# class accountsAdminManagerCreationSerializers(serializers.ModelSerializer):
#     attendance_image = accountsAdminUserAttendanceImageSerializer(required=True, write_only=True)
#     user_profile =accountsAdminUserMainDataSerializers(required=True,write_only=True)
#     assigned_users = accountsAdminSupervisorUsersSerializers(required=False,write_only=True)
#     project = serializers.IntegerField(required=True,write_only=True)
#     location = accountsAdminSupervisorLocationsSerializers(required=True,write_only=True)
#     otp = serializers.IntegerField(required=True,write_only=True)
#
#     class Meta:
#         model = accountsUserProfileModel
#         fields = "__all__"
#
#     def create(self, validated_data):
#         initial_data = validated_data
#         user_profile = validated_data.pop("user_profile")
#         try:
#             assigned_users = validated_data.pop("assigned_users")
#         except:
#             pass
#         project = validated_data.pop("project")
#         location_data = validated_data.pop("location")
#         otp = validated_data.pop("otp")
#         user_att_image = validated_data.pop("attendance_image")
#
#         final_verification = accountsAdminUserCreationLoginOtpModel.objects.filter(phone_number=user_profile["phone_number"], otp=otp,active=True)
#         if final_verification:
#             try:
#                 owner = get_user_model().objects.create_manager(**user_profile)
#                 try:
#                     user_sub_profile = accountsUserProfileModel.objects.create(user_profile=owner,**validated_data)
#                 except Exception as e:
#                     user_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=owner,**user_att_image)
#                 except Exception as e:
#                     owner.delete()
#                     user_sub_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     if len(assigned_users["assigned_users"]) != 0:
#                         try:
#                             main_assigned_users = attendanceUserAttendanceInChargeModel.objects.create(owner=owner)
#                             main_assigned_users.assigned_users.set(assigned_users["assigned_users"])
#                             main_assigned_users.save()
#                         except:
#                             owner.delete()
#                             user_sub_profile.delete()
#                             user_attendance_image.delete()
#                             raise serializers.ValidationError({f"something wrong with assigning users to supervisor"})
#                 except:
#                     pass
#                 try:
#                     assigning_project = projectsPAttendanceUsersModel.objects.get(project__id=project)
#                     assigning_project.owner.add(owner)
#                     assigning_project.save()
#                 except:
#                     try:
#                         exsisting_project = projectsPModel.objects.get(id=project)
#                         main_project = projectsPAttendanceUsersModel.objects.create(project=exsisting_project)
#                         main_project.owner.add(owner)
#                         main_project.save()
#                     except:
#                         try:
#                             main_assigned_users.delete()
#                         except:
#                             pass
#                         owner.delete()
#                         user_sub_profile.delete()
#                         user_attendance_image.delete()
#                         raise serializers.ValidationError({"something wrong with assigning users to Project"})
#
#                 try:
#                     supervisor_location = attendanceUserAttendanceLocationsModel.objects.create(location=location_data["location"],owner=owner)
#                 except:
#                     try:
#                         main_project.delete()
#                     except:
#                         pass
#                     try:
#                         main_assigned_users.delete()
#                     except:
#                         pass
#                     owner.delete()
#                     user_sub_profile.delete()
#                     user_attendance_image.delete()
#                     raise serializers.ValidationError({"something wrong with assigning users to Location"})
#
#             except Exception as e:
#                 print(e)
#                 raise serializers.ValidationError({f"something wrong with user creation ==> {e}"})
#             return initial_data
#         else:
#             raise serializers.ValidationError({"otp": "OTP is not valid"})
#
#
# ##EMPLOYEE CREATION
# class accountsAdminEmployeeCreationSerializers(serializers.ModelSerializer):
#     attendance_image = accountsAdminUserAttendanceImageSerializer(required=True, write_only=True)
#     user_profile =accountsAdminUserMainDataSerializers(required=True,write_only=True)
#     otp = serializers.IntegerField(required=True,write_only=True)
#     assigned_users = accountsAdminSupervisorUsersSerializers(required=False,write_only=True)
#     project = serializers.IntegerField(required=True,write_only=True)
#     location = accountsAdminSupervisorLocationsSerializers(required=True,write_only=True)
#
#     class Meta:
#         model = accountsUserProfileModel
#         fields = "__all__"
#
#     def create(self, validated_data):
#         initial_data = validated_data
#         user_profile = validated_data.pop("user_profile")
#         try:
#             assigned_users = validated_data.pop("assigned_users")
#         except:
#             pass
#         project = validated_data.pop("project")
#         location_data = validated_data.pop("location")
#         otp = validated_data.pop("otp")
#         user_att_image = validated_data.pop("attendance_image")
#
#         final_verification = accountsAdminUserCreationLoginOtpModel.objects.filter(phone_number=user_profile["phone_number"], otp=otp,active=True)
#         if final_verification:
#             try:
#                 owner = get_user_model().objects.create_employee(**user_profile)
#                 try:
#                     user_sub_profile = accountsUserProfileModel.objects.create(user_profile=owner,**validated_data)
#                 except Exception as e:
#                     user_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=owner,**user_att_image)
#                 except Exception as e:
#                     owner.delete()
#                     user_sub_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     if len(assigned_users["assigned_users"]) != 0:
#                         try:
#                             main_assigned_users = attendanceUserAttendanceInChargeModel.objects.create(owner=owner)
#                             main_assigned_users.assigned_users.set(assigned_users["assigned_users"])
#                             main_assigned_users.save()
#                         except:
#                             owner.delete()
#                             user_sub_profile.delete()
#                             user_attendance_image.delete()
#                             raise serializers.ValidationError({f"something wrong with assigning users to supervisor"})
#                 except:
#                     pass
#                 try:
#                     assigning_project = projectsPAttendanceUsersModel.objects.get(project__id=project)
#                     assigning_project.owner.add(owner)
#                     assigning_project.save()
#                 except:
#                     try:
#                         exsisting_project = projectsPModel.objects.get(id=project)
#                         main_project = projectsPAttendanceUsersModel.objects.create(project=exsisting_project)
#                         main_project.owner.add(owner)
#                         main_project.save()
#                     except:
#                         try:
#                             main_assigned_users.delete()
#                         except:
#                             pass
#                         owner.delete()
#                         user_sub_profile.delete()
#                         user_attendance_image.delete()
#                         raise serializers.ValidationError({"something wrong with assigning users to Project"})
#
#                 try:
#                     supervisor_location = attendanceUserAttendanceLocationsModel.objects.create(location=location_data["location"],owner=owner)
#                 except:
#                     try:
#                         main_project.delete()
#                     except:
#                         pass
#                     try:
#                         main_assigned_users.delete()
#                     except:
#                         pass
#                     owner.delete()
#                     user_sub_profile.delete()
#                     user_attendance_image.delete()
#                     raise serializers.ValidationError({"something wrong with assigning users to Location"})
#
#             except Exception as e:
#                 print(e)
#                 raise serializers.ValidationError({f"something wrong with user creation ==> {e}"})
#             return initial_data
#         else:
#             raise serializers.ValidationError({"otp": "OTP is not valid"})
#
# ##STORE MANAGER CREATION
# class accountsAdminStoreManagerCreationSerializers(serializers.ModelSerializer):
#     attendance_image = accountsAdminUserAttendanceImageSerializer(required=True, write_only=True)
#     user_profile =accountsAdminUserMainDataSerializers(required=True,write_only=True)
#     otp = serializers.IntegerField(required=True,write_only=True)
#     assigned_users = accountsAdminSupervisorUsersSerializers(required=False, write_only=True)
#     project = serializers.IntegerField(required=True, write_only=True)
#     location = accountsAdminSupervisorLocationsSerializers(required=True, write_only=True)
#
#     class Meta:
#         model = accountsUserProfileModel
#         fields = "__all__"
#
#     def create(self, validated_data):
#         initial_data = validated_data
#         user_profile = validated_data.pop("user_profile")
#         try:
#             assigned_users = validated_data.pop("assigned_users")
#         except:
#             pass
#         project = validated_data.pop("project")
#         location_data = validated_data.pop("location")
#         otp = validated_data.pop("otp")
#         user_att_image = validated_data.pop("attendance_image")
#
#         final_verification = accountsAdminUserCreationLoginOtpModel.objects.filter(
#             phone_number=user_profile["phone_number"], otp=otp, active=True)
#         if final_verification:
#             try:
#                 owner = get_user_model().objects.create_store_manager(**user_profile)
#                 try:
#                     user_sub_profile = accountsUserProfileModel.objects.create(user_profile=owner, **validated_data)
#                 except Exception as e:
#                     user_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=owner,
#                                                                                               **user_att_image)
#                 except Exception as e:
#                     owner.delete()
#                     user_sub_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     if len(assigned_users["assigned_users"]) != 0:
#                         try:
#                             main_assigned_users = attendanceUserAttendanceInChargeModel.objects.create(owner=owner)
#                             main_assigned_users.assigned_users.set(assigned_users["assigned_users"])
#                             main_assigned_users.save()
#                         except:
#                             owner.delete()
#                             user_sub_profile.delete()
#                             user_attendance_image.delete()
#                             raise serializers.ValidationError({f"something wrong with assigning users to supervisor"})
#                 except:
#                     pass
#                 try:
#                     assigning_project = projectsPAttendanceUsersModel.objects.get(project__id=project)
#                     assigning_project.owner.add(owner)
#                     assigning_project.save()
#                 except:
#                     try:
#                         exsisting_project = projectsPModel.objects.get(id=project)
#                         main_project = projectsPAttendanceUsersModel.objects.create(project=exsisting_project)
#                         main_project.owner.add(owner)
#                         main_project.save()
#                     except:
#                         try:
#                             main_assigned_users.delete()
#                         except:
#                             pass
#                         owner.delete()
#                         user_sub_profile.delete()
#                         user_attendance_image.delete()
#                         raise serializers.ValidationError({"something wrong with assigning users to Project"})
#
#                 try:
#                     supervisor_location = attendanceUserAttendanceLocationsModel.objects.create(
#                         location=location_data["location"], owner=owner)
#                 except:
#                     try:
#                         main_project.delete()
#                     except:
#                         pass
#                     try:
#                         main_assigned_users.delete()
#                     except:
#                         pass
#                     owner.delete()
#                     user_sub_profile.delete()
#                     user_attendance_image.delete()
#                     raise serializers.ValidationError({"something wrong with assigning users to Location"})
#
#             except Exception as e:
#                 print(e)
#                 raise serializers.ValidationError({f"something wrong with user creation ==> {e}"})
#             return initial_data
#         else:
#             raise serializers.ValidationError({"otp": "OTP is not valid"})
#
#
# ##ENGINEER CREATION
# class accountsAdminEngineerCreationSerializers(serializers.ModelSerializer):
#     attendance_image = accountsAdminUserAttendanceImageSerializer(required=True, write_only=True)
#     user_profile =accountsAdminUserMainDataSerializers(required=True,write_only=True)
#     otp = serializers.IntegerField(required=True,write_only=True)
#     assigned_users = accountsAdminSupervisorUsersSerializers(required=False, write_only=True)
#     project = serializers.IntegerField(required=True, write_only=True)
#     location = accountsAdminSupervisorLocationsSerializers(required=True, write_only=True)
#
#     class Meta:
#         model = accountsUserProfileModel
#         fields = "__all__"
#
#     def create(self, validated_data):
#         initial_data = validated_data
#         user_profile = validated_data.pop("user_profile")
#         try:
#             assigned_users = validated_data.pop("assigned_users")
#         except:
#             pass
#         project = validated_data.pop("project")
#         location_data = validated_data.pop("location")
#         otp = validated_data.pop("otp")
#         user_att_image = validated_data.pop("attendance_image")
#
#         final_verification = accountsAdminUserCreationLoginOtpModel.objects.filter(
#             phone_number=user_profile["phone_number"], otp=otp, active=True)
#         if final_verification:
#             try:
#                 owner = get_user_model().objects.create_engineer(**user_profile)
#                 try:
#                     user_sub_profile = accountsUserProfileModel.objects.create(user_profile=owner, **validated_data)
#                 except Exception as e:
#                     user_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=owner,
#                                                                                               **user_att_image)
#                 except Exception as e:
#                     owner.delete()
#                     user_sub_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     if len(assigned_users["assigned_users"]) != 0:
#                         try:
#                             main_assigned_users = attendanceUserAttendanceInChargeModel.objects.create(owner=owner)
#                             main_assigned_users.assigned_users.set(assigned_users["assigned_users"])
#                             main_assigned_users.save()
#                         except:
#                             owner.delete()
#                             user_sub_profile.delete()
#                             user_attendance_image.delete()
#                             raise serializers.ValidationError({f"something wrong with assigning users to supervisor"})
#                 except:
#                     pass
#
#                 try:
#                     assigning_project = projectsPAttendanceUsersModel.objects.get(project__id=project)
#                     assigning_project.owner.add(owner)
#                     assigning_project.save()
#                 except:
#                     try:
#                         exsisting_project = projectsPModel.objects.get(id=project)
#                         main_project = projectsPAttendanceUsersModel.objects.create(project=exsisting_project)
#                         main_project.owner.add(owner)
#                         main_project.save()
#                     except:
#                         try:
#                             main_assigned_users.delete()
#                         except:
#                             pass
#                         owner.delete()
#                         user_sub_profile.delete()
#                         user_attendance_image.delete()
#                         raise serializers.ValidationError({"something wrong with assigning users to Project"})
#
#                 try:
#                     supervisor_location = attendanceUserAttendanceLocationsModel.objects.create(
#                         location=location_data["location"], owner=owner)
#                 except:
#                     try:
#                         main_project.delete()
#                     except:
#                         pass
#                     try:
#                         main_assigned_users.delete()
#                     except:
#                         pass
#                     owner.delete()
#                     user_sub_profile.delete()
#                     user_attendance_image.delete()
#                     raise serializers.ValidationError({"something wrong with assigning users to Location"})
#
#             except Exception as e:
#                 print(e)
#                 raise serializers.ValidationError({f"something wrong with user creation ==> {e}"})
#             return initial_data
#         else:
#             raise serializers.ValidationError({"otp": "OTP is not valid"})
#
#
# ##FINANCE CREATION
# class accountsAdminFinanceCreationSerializers(serializers.ModelSerializer):
#     attendance_image = accountsAdminUserAttendanceImageSerializer(required=True, write_only=True)
#     user_profile = accountsAdminUserMainDataSerializers(required=True, write_only=True)
#     otp = serializers.IntegerField(required=True, write_only=True)
#     assigned_users = accountsAdminSupervisorUsersSerializers(required=False, write_only=True)
#     project = serializers.IntegerField(required=True, write_only=True)
#     location = accountsAdminSupervisorLocationsSerializers(required=True, write_only=True)
#
#     class Meta:
#         model = accountsUserProfileModel
#         fields = "__all__"
#
#     def create(self, validated_data):
#         initial_data = validated_data
#         user_profile = validated_data.pop("user_profile")
#         try:
#             assigned_users = validated_data.pop("assigned_users")
#         except:
#             pass
#         project = validated_data.pop("project")
#         location_data = validated_data.pop("location")
#         otp = validated_data.pop("otp")
#         user_att_image = validated_data.pop("attendance_image")
#
#         final_verification = accountsAdminUserCreationLoginOtpModel.objects.filter(
#             phone_number=user_profile["phone_number"], otp=otp, active=True)
#         if final_verification:
#             try:
#                 owner = get_user_model().objects.create_finance(**user_profile)
#                 try:
#                     user_sub_profile = accountsUserProfileModel.objects.create(user_profile=owner, **validated_data)
#                 except Exception as e:
#                     user_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=owner,
#                                                                                               **user_att_image)
#                 except Exception as e:
#                     owner.delete()
#                     user_sub_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     if len(assigned_users["assigned_users"]) != 0:
#                         try:
#                             main_assigned_users = attendanceUserAttendanceInChargeModel.objects.create(owner=owner)
#                             main_assigned_users.assigned_users.set(assigned_users["assigned_users"])
#                             main_assigned_users.save()
#                         except:
#                             owner.delete()
#                             user_sub_profile.delete()
#                             user_attendance_image.delete()
#                             raise serializers.ValidationError({f"something wrong with assigning users to supervisor"})
#                 except:
#                     pass
#
#                 try:
#                     assigning_project = projectsPAttendanceUsersModel.objects.get(project__id=project)
#                     assigning_project.owner.add(owner)
#                     assigning_project.save()
#                 except:
#                     try:
#                         exsisting_project = projectsPModel.objects.get(id=project)
#                         main_project = projectsPAttendanceUsersModel.objects.create(project=exsisting_project)
#                         main_project.owner.add(owner)
#                         main_project.save()
#                     except:
#                         try:
#                             main_assigned_users.delete()
#                         except:
#                             pass
#                         owner.delete()
#                         user_sub_profile.delete()
#                         user_attendance_image.delete()
#                         raise serializers.ValidationError({"something wrong with assigning users to Project"})
#
#                 try:
#                     supervisor_location = attendanceUserAttendanceLocationsModel.objects.create(
#                         location=location_data["location"], owner=owner)
#                 except:
#                     try:
#                         main_project.delete()
#                     except:
#                         pass
#                     try:
#                         main_assigned_users.delete()
#                     except:
#                         pass
#                     owner.delete()
#                     user_sub_profile.delete()
#                     user_attendance_image.delete()
#                     raise serializers.ValidationError({"something wrong with assigning users to Location"})
#
#             except Exception as e:
#                 print(e)
#                 raise serializers.ValidationError({f"something wrong with user creation ==> {e}"})
#             return initial_data
#         else:
#             raise serializers.ValidationError({"otp": "OTP is not valid"})
#
#
# ##HEAD OFFICE CREATION
# class accountsAdminHeadOfficeCreationSerializers(serializers.ModelSerializer):
#     attendance_image = accountsAdminUserAttendanceImageSerializer(required=True, write_only=True)
#     user_profile = accountsAdminUserMainDataSerializers(required=True, write_only=True)
#     otp = serializers.IntegerField(required=True, write_only=True)
#     assigned_users = accountsAdminSupervisorUsersSerializers(required=False, write_only=True)
#     project = serializers.IntegerField(required=True, write_only=True)
#     location = accountsAdminSupervisorLocationsSerializers(required=True, write_only=True)
#
#     class Meta:
#         model = accountsUserProfileModel
#         fields = "__all__"
#
#     def create(self, validated_data):
#         initial_data = validated_data
#         user_profile = validated_data.pop("user_profile")
#         try:
#             assigned_users = validated_data.pop("assigned_users")
#         except:
#             pass
#         project = validated_data.pop("project")
#         location_data = validated_data.pop("location")
#         otp = validated_data.pop("otp")
#         user_att_image = validated_data.pop("attendance_image")
#
#         final_verification = accountsAdminUserCreationLoginOtpModel.objects.filter(
#             phone_number=user_profile["phone_number"], otp=otp, active=True)
#         if final_verification:
#             try:
#                 owner = get_user_model().objects.create_head_office(**user_profile)
#                 try:
#                     user_sub_profile = accountsUserProfileModel.objects.create(user_profile=owner, **validated_data)
#                 except Exception as e:
#                     user_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=owner,
#                                                                                               **user_att_image)
#                 except Exception as e:
#                     owner.delete()
#                     user_sub_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     if len(assigned_users["assigned_users"]) != 0:
#                         try:
#                             main_assigned_users = attendanceUserAttendanceInChargeModel.objects.create(owner=owner)
#                             main_assigned_users.assigned_users.set(assigned_users["assigned_users"])
#                             main_assigned_users.save()
#                         except:
#                             owner.delete()
#                             user_sub_profile.delete()
#                             user_attendance_image.delete()
#                             raise serializers.ValidationError({f"something wrong with assigning users to supervisor"})
#                 except:
#                     pass
#
#                 try:
#                     assigning_project = projectsPAttendanceUsersModel.objects.get(project__id=project)
#                     assigning_project.owner.add(owner)
#                     assigning_project.save()
#                 except:
#                     try:
#                         exsisting_project = projectsPModel.objects.get(id=project)
#                         main_project = projectsPAttendanceUsersModel.objects.create(project=exsisting_project)
#                         main_project.owner.add(owner)
#                         main_project.save()
#                     except:
#                         try:
#                             main_assigned_users.delete()
#                         except:
#                             pass
#                         owner.delete()
#                         user_sub_profile.delete()
#                         user_attendance_image.delete()
#                         raise serializers.ValidationError({"something wrong with assigning users to Project"})
#
#                 try:
#                     supervisor_location = attendanceUserAttendanceLocationsModel.objects.create(
#                         location=location_data["location"], owner=owner)
#                 except:
#                     try:
#                         main_project.delete()
#                     except:
#                         pass
#                     try:
#                         main_assigned_users.delete()
#                     except:
#                         pass
#                     owner.delete()
#                     user_sub_profile.delete()
#                     user_attendance_image.delete()
#                     raise serializers.ValidationError({"something wrong with assigning users to Location"})
#
#             except Exception as e:
#                 print(e)
#                 raise serializers.ValidationError({f"something wrong with user creation ==> {e}"})
#             return initial_data
#         else:
#             raise serializers.ValidationError({"otp": "OTP is not valid"})
#
#
# ##MAIN OWNER CREATION
# class accountsAdminMainOwnerCreationSerializers(serializers.ModelSerializer):
#     attendance_image = accountsAdminUserAttendanceImageSerializer(required=True, write_only=True)
#     user_profile = accountsAdminUserMainDataSerializers(required=True, write_only=True)
#     otp = serializers.IntegerField(required=True, write_only=True)
#     assigned_users = accountsAdminSupervisorUsersSerializers(required=False, write_only=True)
#     project = serializers.IntegerField(required=True, write_only=True)
#     location = accountsAdminSupervisorLocationsSerializers(required=True, write_only=True)
#
#     class Meta:
#         model = accountsUserProfileModel
#         fields = "__all__"
#
#     def create(self, validated_data):
#         initial_data = validated_data
#         user_profile = validated_data.pop("user_profile")
#         try:
#             assigned_users = validated_data.pop("assigned_users")
#         except:
#             pass
#         project = validated_data.pop("project")
#         location_data = validated_data.pop("location")
#         otp = validated_data.pop("otp")
#         user_att_image = validated_data.pop("attendance_image")
#
#         final_verification = accountsAdminUserCreationLoginOtpModel.objects.filter(
#             phone_number=user_profile["phone_number"], otp=otp, active=True)
#         if final_verification:
#             try:
#                 owner = get_user_model().objects.create_main_owner(**user_profile)
#                 try:
#                     user_sub_profile = accountsUserProfileModel.objects.create(user_profile=owner, **validated_data)
#                 except Exception as e:
#                     user_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=owner,
#                                                                                               **user_att_image)
#                 except Exception as e:
#                     owner.delete()
#                     user_sub_profile.delete()
#                     raise serializers.ValidationError({"something wrong with user user_sub_profile"})
#
#                 try:
#                     if len(assigned_users["assigned_users"]) != 0:
#                         try:
#                             main_assigned_users = attendanceUserAttendanceInChargeModel.objects.create(owner=owner)
#                             main_assigned_users.assigned_users.set(assigned_users["assigned_users"])
#                             main_assigned_users.save()
#                         except:
#                             owner.delete()
#                             user_sub_profile.delete()
#                             user_attendance_image.delete()
#                             raise serializers.ValidationError({f"something wrong with assigning users to supervisor"})
#                 except:
#                     pass
#                 try:
#                     assigning_project = projectsPAttendanceUsersModel.objects.get(project__id=project)
#                     assigning_project.owner.add(owner)
#                     assigning_project.save()
#                 except:
#                     try:
#                         exsisting_project = projectsPModel.objects.get(id=project)
#                         main_project = projectsPAttendanceUsersModel.objects.create(project=exsisting_project)
#                         main_project.owner.add(owner)
#                         main_project.save()
#                     except:
#                         try:
#                             main_assigned_users.delete()
#                         except:
#                             pass
#                         owner.delete()
#                         user_sub_profile.delete()
#                         user_attendance_image.delete()
#                         raise serializers.ValidationError({"something wrong with assigning users to Project"})
#
#                 try:
#                     supervisor_location = attendanceUserAttendanceLocationsModel.objects.create(
#                         location=location_data["location"], owner=owner)
#                 except:
#                     try:
#                         main_project.delete()
#                     except:
#                         pass
#                     try:
#                         main_assigned_users.delete()
#                     except:
#                         pass
#                     owner.delete()
#                     user_sub_profile.delete()
#                     user_attendance_image.delete()
#                     raise serializers.ValidationError({"something wrong with assigning users to Location"})
#
#             except Exception as e:
#                 print(e)
#                 raise serializers.ValidationError({f"something wrong with user creation ==> {e}"})
#             return initial_data
#         else:
#             raise serializers.ValidationError({"otp": "OTP is not valid"})
#
#
# class accountsAdminLoginUserAttendanceStatsSerializers(serializers.ModelSerializer):
#     over_all_attendance_stats = serializers.SerializerMethodField(read_only=True)
#
#     def get_over_all_attendance_stats(self,obj):
#         over_all_attendance_stats = {}
#         today_date = datetime.today().date()
#         attendance_main = obj.attendanceUserAttendanceMainModel_owner.all()
#         approved_attendance = obj.attendanceUserAttendanceMainModel_owner.filter(approved="APPROVED")
#         unapproved_attendance = obj.attendanceUserAttendanceMainModel_owner.filter(approved="UNAPPROVED")
#         try:
#             start_date = attendance_main.last().created_at.date()
#         except:
#             start_date = today_date
#         over_all_attendance = len(attendance_main)
#         over_all_attendance_stats["total_attendance"] = over_all_attendance
#         over_all_attendance_stats["total_approved_attendance"] = len(approved_attendance)
#         over_all_attendance_stats["total_unapproved_attendance"] = len(unapproved_attendance)
#         over_all_attendance_stats["total_days"] = (today_date - start_date).days
#         over_all_attendance_stats["total_presents"] = over_all_attendance_stats["total_approved_attendance"]
#         over_all_attendance_stats["total_absents"] = over_all_attendance_stats["total_days"] - over_all_attendance_stats["total_approved_attendance"]
#         return over_all_attendance_stats
#
#     class Meta:
#         model = get_user_model()
#         fields = ["id","phone_number","employee_id","email","slug","over_all_attendance_stats",]
#
# ##USERS SPECIFIC PROJECTS
# class accountsAdminUsersProjectsSerializers(serializers.ModelSerializer):
#     class Meta:
#         model = projectsPModel
#         fields = "__all__"
#
# class accountsAdminUsersProjectsRoadSerializers(serializers.ModelSerializer):
#     class Meta:
#         model = projectsRoadModel
#         fields = "__all__"
#
# class accountsAdminUsersProjectsRoadLatLonSerializers(serializers.ModelSerializer):
#     class Meta:
#         model = projectsRoadsLatLonModel
#         fields = "__all__"
#
# class accountsAdminUserSpecificProjectsSerializers(serializers.ModelSerializer):
#     projects = serializers.SerializerMethodField(read_only=True)
#
#     def get_projects(self,obj):
#         details = {}
#         projects_data = []
#         lat_lon_serializer = []
#         project_road = []
#         projects = obj.projectsPAttendanceUsersModel_owner.all()
#         for main_project in projects:
#             final_project = main_project.project
#             projects_data.append(final_project)
#         for project in projects_data:
#             project_road_data = project.projectsRoadModel_project.all()
#             for project_lat_lon in project_road_data:
#                 lat_lon = project_lat_lon.projectsRoadsLatLonModel_road.all()
#                 # lat_lon_serializer = accountsAdminUsersProjectsRoadLatLonSerializers((lat_lon),many=True).data
#             project_road = accountsAdminUsersProjectsRoadSerializers((project_road_data),many=True).data
#         serializer = accountsAdminUsersProjectsSerializers((projects_data),many=True).data
#         # details["lat_lon"] = lat_lon_serializer
#         details["roads"] = project_road
#         details["projects"] = serializer
#         return details
#
#     class Meta:
#         model = get_user_model()
#         fields = ["projects","id","phone_number","employee_id","email","slug",]
#
# class accountsAdminUserWalletSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = bitgoUserWalletModel
#         fields = "__all__"

class userPhoneCheckSerializer(serializers.Serializer):
    phone = serializers.IntegerField(required=True)
    data = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        phone = data.get("phone", None)
        user = get_user_model().objects.filter(phone_number=phone)
        if user.last().is_admin:
            pass
        else:
            raise serializers.ValidationError(
                {"message": "You Are Not Having Access To Go Through Dashboard", 'status': status.HTTP_400_BAD_REQUEST})
        if user.count() == 0:
            raise serializers.ValidationError(
                {"message": "A User with this Phone is not found.", 'status': status.HTTP_400_BAD_REQUEST})

        final_otp = random.randint(1000, 9999)
        try:
            try:
                send_message_otp(phone, final_otp)
            except:
                raise serializers.ValidationError(
                    {"message": "unable to send otp", "status": status.HTTP_400_BAD_REQUEST})
            accountsUserLoginOtpModel.objects.create(owner=user.first(), otp=final_otp)
        except:
            raise serializers.ValidationError(
                'otp failed'
            )

        return {
            'phone': phone,
            'data': True
        }


class UserLoginSerializer(serializers.Serializer):
    phone = serializers.IntegerField(required=True)
    otp = serializers.IntegerField(write_only=True, required=True)
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
                "message": 'A user with this Phone is not found.'})
        user = user.first()
        if user.accountsUserLoginOtpModel_user.filter(active=True, otp=otp):
            pass
        else:
            raise serializers.ValidationError({"message": 'Please enter a valid OTP'})
        # user = authenticate(phone=user.phone_number, password=user.password)
        if user is None:
            raise serializers.ValidationError(
                'A user with this email and password is not found.'
            )
        jwt_token = get_tokens_for_user(user)
        print(phone, phone)
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
            'phone': user.phone_number,
            'access': jwt_token["access"],
            'refresh': jwt_token["refresh"],
            # 'cricket_refresh':data["refresh"],
            # 'cricket_access':data["access"],
        }


class UserCheckAndcreationSerializer(serializers.Serializer):
    phone = serializers.IntegerField(required=True)
    email = serializers.EmailField(required=False)
    name = serializers.CharField(max_length=200, required=True)
    referal_code = serializers.CharField(max_length=50, required=False)
    date_of_birth = serializers.DateField(required=True)

    def validate(self, data):
        phone = data.get("phone")
        email = data.get("email", None)
        name = data.get("name")
        referal_code = data.get("referal_code", None)

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
            raise serializers.ValidationError({"message": "A user with this Phone already exists"})

        if difference_in_years < 18:
            raise serializers.ValidationError({"message": "Minors Are Not Allowed To Play The Game"})
        else:
            pass
        if referal_code == None:
            try:
                user_creation = get_user_model().objects.create_employee(phone_number=phone, password=str(phone))
                # user_creation.name = name
                user_creation.email = email
                user_creation.save()

                try:
                    user_profile = accountsUserProfileModel.objects.create(user_profile=user_creation,
                                                                           name=name,
                                                                           date_of_birth=birthday,
                                                                           user_game_name=name + str(
                                                                               random.randint(1000, 9999)))
                except Exception as e:
                    user_creation.delete()
                    raise serializers.ValidationError(
                        {"message": f"unable to create profile {e}", "status": status.HTTP_400_BAD_REQUEST})
                try:
                    # user_name = name
                    splited_name = name.split()
                    code = splited_name[0].upper() + str(user_creation.id) + get_random_string(5,
                                                                                               string.ascii_uppercase + string.digits)
                    user_referal_code = accountsUserReferalCodeModel.objects.create(owner=user_creation,
                                                                                    referal_code=referal_code_generator(
                                                                                        user_creation))
                except Exception as e:
                    user_creation.delete()
                    user_profile.delete()
                    raise serializers.ValidationError(
                        {"message": f"unable to create referal code {e}", "status": status.HTTP_400_BAD_REQUEST})
                try:
                    user_email = accountsUserEmailUpdateModel.objects.create(owner=user_creation, email=email)
                except Exception as e:
                    user_creation.delete()
                    user_profile.delete()
                    user_referal_code.delete()
                    raise serializers.ValidationError(
                        {"message": f"unable to create email code {e}", "status": status.HTTP_400_BAD_REQUEST})
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
                    raise serializers.ValidationError(
                        {"message": f"unable to create account {e}", "status": status.HTTP_400_BAD_REQUEST})
            except Exception as e:
                raise serializers.ValidationError(
                    {"message": f"unable to create account {e}", "status": status.HTTP_400_BAD_REQUEST})
        else:
            code = accountsUserReferalCodeModel.objects.filter(referal_code=referal_code).last()
            if code:
                pass
            else:
                raise serializers.ValidationError({"message": "Please Enter A Valid Referal Code"})
            try:
                user_creation = get_user_model().objects.create_employee(phone_number=phone, password=str(phone))
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
                                                                           user_game_name=name + str(
                                                                               random.randint(1000, 9999)))
                except:
                    user_creation.delete()
                    code.no_of_times -= 1
                    code.save()
                    code.users_used.remove(user_creation)
                    raise serializers.ValidationError(
                        {"message": "unable to create profile", "status": status.HTTP_400_BAD_REQUEST})
                try:
                    splited_name = name.split()
                    code = splited_name[0].upper() + str(user_creation.id) + get_random_string(5,
                                                                                               string.ascii_uppercase + string.digits)
                    user_referal_code = accountsUserReferalCodeModel.objects.create(owner=user_creation,
                                                                                    referal_code=referal_code_generator(
                                                                                        user_creation))
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
            'phone': phone,
            'date_of_birth': birthday
        }


class accountsUserPhonePasswordLoginSerializer(serializers.Serializer):
    employee_id = serializers.CharField(max_length=150, required=True)
    # otp = serializers.IntegerField(write_only=True, required=True)
    # email = serializers.EmailField(required=True)
    password = serializers.CharField(max_length=100, required=True)
    access = serializers.CharField(max_length=255, read_only=True)
    refresh = serializers.CharField(max_length=255, read_only=True)
    name = serializers.CharField(max_length=75, read_only=True)
    image = serializers.ImageField(read_only=True)

    def validate(self, data):
        main_employee_id = data.get("employee_id", None)
        main_password = data.get("password", None)

        user = get_user_model().objects.filter(employee_id=main_employee_id)
        if user:
            pass
        else:

            raise serializers.ValidationError(
                {"user": "A user with this Phone is not found.", 'status': status.HTTP_400_BAD_REQUEST})
        main_user = user.first()
        # user_validation = authenticate(email=main_email,password=main_password)
        # if user_validation:
        #     pass
        # else:
        #     raise serializers.ValidationError(
        #         'Please enter a valid Password'
        #     )
        main_user_pass = main_user.password
        result_data = check_password(main_password, main_user_pass)
        if result_data is False:
            raise serializers.ValidationError(
                {"user": "A user with this Phone and password is not found.", 'status': status.HTTP_400_BAD_REQUEST})

        jwt_token = get_tokens_for_user(main_user)

        return {
            # 'name':user.get_employees_name(),
            # 'image':user.get_user_image(),
            'employee_id': main_user.employee_id,
            'password': main_user.email,
            'access': jwt_token["access"],
            'refresh': jwt_token["refresh"],
        }

    class Meta:
        fields = "__all__"


"new add"
"""
log in and token
"""


# class UserLoginSerializer(serializers.Serializer):
#
#     phone = serializers.IntegerField(required=True)
#     otp = serializers.IntegerField(write_only=True,required=True)
#     access = serializers.CharField(max_length=255, read_only=True)
#     refresh = serializers.CharField(max_length=255, read_only=True)
#     name = serializers.CharField(max_length=75, read_only=True)
#     image = serializers.ImageField(read_only=True)
#
#     def validate(self, data):
#         phone = data.get("phone", None)
#         otp = data.get("otp", None)
#         user = get_user_model().objects.filter(phone_number=phone)
#         if user:
#             pass
#         else:
#             raise serializers.ValidationError(
#                 'A user with this Phone is not found.'
#             )
#         user = user.first()
#         if user.accountsUserLoginOtpModel_user.filter(active=True,otp=otp):
#             pass
#         else:
#             raise serializers.ValidationError(
#                 'Please enter a valid OTP'
#             )
#         # user = authenticate(phone=user.phone_number, password=user.password)
#         if user is None:
#             raise serializers.ValidationError(
#                 'A user with this email and password is not found.'
#             )
#         jwt_token = get_tokens_for_user(user)
#         return {
#             # 'name':user.get_employees_name(),
#             # 'image':user.get_user_image(),
#             'phone':user.phone_number,
#             'access': jwt_token["access"],
#             'refresh':jwt_token["refresh"],
#         }
#

# new add



# <editor-fold desc="Serializer For Get all User Permissions And Update">
class accountsAdminUserPermissionsSerializer(serializers.ModelSerializer):
    """
    http://192.168.1.8:3001/profile
    View/Edit User Permission
    """
    class Meta:
        model = get_user_model()
        fields = ["is_employee", "is_supervisor", "is_store_manager", "is_gaurage_manager","is_project_manager","is_project_coordinator","is_head_office","is_main_owner"]

# </editor-fold>

# # <editor-fold desc="Serializer For Get View detail user">
#
# class accountsAdminViewUserProfileDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = accountsUserProfileModel
#         fields ='__all__'
# class accountsAdminViewUserAddressDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = accountsUserAddressModel
#         fields = '__all__'
# class accountsAdminViewUserAttendanceImageDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = attendanceUserAttendanceImageModel
#         fields = '__all__'
#
# class accountsAdminViewUserProjectSerializers(serializers.ModelSerializer):
#     class Meta:
#         model=projectsPModel
#         fields='__all__'
# class accountsAdminViewUserAttendanceUsersDetailSerializer(serializers.ModelSerializer):
#     project=accountsAdminViewUserProjectSerializers(source="projectsPAttendanceUsersModel_project")
#     class Meta:
#         model = projectsPAttendanceUsersModel
#         fields = '__all__'
# class accountsAdminViewUserAttendanceLocationsDetailSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = attendanceUserAttendanceLocationsModel
#         fields = '__all__'
#
#
# class accountsAdminViewUserDetailSerializer(serializers.ModelSerializer):
#
#     user_profile=accountsAdminViewUserProfileDetailSerializer(source="accountsUserProfileModel_owner")
#     user_address=accountsAdminViewUserAddressDetailSerializer(source="accountsUserAddressModel_owner")
#
#     attendance_images = accountsAdminViewUserAttendanceImageDetailSerializer(source="attendanceUserAttendanceImageModel_owner",many=True)
#
#     user_attendance_location=accountsAdminViewUserAttendanceLocationsDetailSerializer(source="attendanceUserAttendanceLocationsModel_owner",many=True)
#
#     user_attendance_detail=serializers.SerializerMethodField(source="projectsPAttendanceUsersModel_owner")
#     # user_attendance_detail=accountsAdminViewUserAttendanceUsersDetailSerializer(source="projectsPAttendanceUsersModel_owner",many=True)
#
#     def get_user_attendance_detail(self,obj):
#         try:
#             user_attendance_detail=accountsAdminViewUserAttendanceUsersDetailSerializer(obj.projectsPAttendanceUsersModel_owner.all(),many=True).data
#         except:
#             user_attendance_detail=[]
#         return user_attendance_detail
#
#
#     # attendance_images = serializers.SerializerMethodField()
#     #
#     # def get_attendance_images(self, obj):
#     #     attendance_images = attendanceUserAttendanceImageModel.objects.filter(owner=obj)
#     #     serializer = accountsAdminViewUserAttendanceImageDetailSerializer(attendance_images, many=True)
#     #     return serializer.data
#     class Meta:
#         model=get_user_model()
#         exclude = ["password", "user_permissions", "groups"]
# # </editor-fold>

# <editor-fold desc="new user detail with attendance data">
class accountsAdminUserProfileAttendanceSerializers(serializers.ModelSerializer):
    owner_details = serializers.SerializerMethodField(read_only=True)
    attendance_details = serializers.SerializerMethodField(read_only=True)
    role = serializers.SerializerMethodField(read_only=True)

    def get_role(self, obj):
        user = user_roles(obj)
        return user

    def get_attendance_details(self,obj):
        attendance_details = {}
        today = datetime.today().date()
        one_week_ago = datetime.today() - timedelta(days=7)
        one_month_ago = datetime.today() - timedelta(days=30)
        attendance = obj.attendanceUserAttendanceMainModel_owner.filter(created_at__gte=one_month_ago,created_at__lte=today,approved="APPROVED")
        attendance_week = obj.attendanceUserAttendanceMainModel_owner.filter(created_at__gte=one_week_ago,
                                                                        created_at__lte=today,approved="APPROVED")
        try:
            locations_name = []
            attendance_today = obj.attendanceUserAttendanceMainModel_owner.filter(created_at__contains=today)
            if len(attendance_today) == 0:
                attendance_details["today_location"] = "ABSENT"
                attendance_details["today_attendance_time"] = "ABSENT"
            for attendance_data in attendance_today:
                attendance_details["today_location"] = attendance_data.ref_location.title
                attendance_details["today_attendance_time"] = attendance_data.attendance_time
        except:
            raise serializers.ValidationError('Error while fetching todays attendance details')
        attendance_details["monthly_presents"] = len(attendance)
        # attendance_details["weekly_details"] = attendance_week.values()
        attendance_details["weekly_presents"] = len(attendance_week)
        return attendance_details

    def get_owner_details(self,obj):
        designations = []
        if obj.is_superuser:
            designations.append("superuser")
        if obj.is_staff:
            designations.append("staff")
        if obj.is_admin:
            designations.append("admin")
        if obj.is_supervisor:
            designations.append("supervisor")
        if obj.is_employee:
            designations.append("employee")
        if obj.is_store_manager:
            designations.append("store_manager")
        if obj.is_gaurage_manager:
            designations.append("garage_manager")
        if obj.is_project_manager:
            designations.append("project_manager")
        if obj.is_project_coordinator:
            designations.append("project_coordinator")
        if obj.is_head_office:
            designations.append("head_office")
        if obj.is_main_owner:
            designations.append("main_owner")

        owner_details = {}
        owner_projects = projectsPAttendanceUsersModel.objects.filter(owner=obj)
        try:
            owner_profile = obj.accountsUserProfileModel_owner
            owner_details["name"] = owner_profile.name
            owner_details["first_name"] = owner_profile.first_name
            owner_details["last_name"] = owner_profile.last_name
            owner_details["date_of_birth"] = owner_profile.date_of_birth
            owner_details["gender"] = owner_profile.gender
            try:
                owner_details["image"] = owner_profile.image.url
            except:
                owner_details["image"] = ""
            owner_details["designation"] = designations
            owner_details["owner_profile_slug"] = owner_profile.slug
            owner_details["projects"] = owner_projects.values("project__title")
        except:
            owner_details = {"name":"","image":"","designation":designations,"owner_profile_slug":"owner_profile_slug","projects":[]}
        return owner_details

    class Meta:
        model = get_user_model()
        exclude = ["password",]
# </editor-fold>

# <editor-fold desc="View user Permissions">
class accountsAdminUsersPermissionsSerializers(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        exclude = ["password","last_login",]
# </editor-fold>

# <editor-fold desc="USERS SPECIFIC LOCATION AND PROJECT">

##USERS SPECIFIC PROJECTS
class accountsAdminUsersProjectsSerializers(serializers.ModelSerializer):
    class Meta:
        model = projectsPModel
        fields = "__all__"

class accountsAdminUsersProjectsRoadSerializers(serializers.ModelSerializer):
    class Meta:
        model = projectsRoadModel
        fields = "__all__"

class accountsAdminUserSpecificProjectsSerializers(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField(read_only=True)

    def get_projects(self,obj):
        details = {}
        projects_data = []
        lat_lon_serializer = []
        project_road = []
        projects = obj.projectsPAttendanceUsersModel_owner.all()
        for main_project in projects:
            final_project = main_project.project
            projects_data.append(final_project)
        for project in projects_data:
            project_road_data = project.projectsRoadModel_project.all()
            for project_lat_lon in project_road_data:
                lat_lon = project_lat_lon.projectsRoadsLatLonModel_road.all()
                # lat_lon_serializer = accountsAdminUsersProjectsRoadLatLonSerializers((lat_lon),many=True).data
            project_road = accountsAdminUsersProjectsRoadSerializers((project_road_data),many=True).data
        serializer = accountsAdminUsersProjectsSerializers((projects_data),many=True).data
        # details["lat_lon"] = lat_lon_serializer
        details["roads"] = project_road
        details["projects"] = serializer
        return details

    class Meta:
        model = get_user_model()
        fields = ["projects","id","phone_number","employee_id","email","slug",]
# </editor-fold>


# new adding
# # <editor-fold desc="Serializer For New Main Owner Create">

class accountAdminMainOwnerProfileSerializer(serializers.ModelSerializer):
    """
    optional
    date_of_birth,gender,image

    """
    class Meta:
        model = accountsUserProfileModel
        exclude = ['date_created', 'owner']


class accountsAdminMainOwnerAddressSerializer(serializers.ModelSerializer):
    """
    optional
        pincode,address_proof
    """
    class Meta:
        model = accountsUserAddressModel
        exclude = ['owner', ]

class accountsAdminMainOwnerAttendanceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = attendanceUserAttendanceImageModel
        exclude = ['owner', ]

class accountsAdminMainOwnerSerializer(serializers.Serializer):
    profile = accountAdminMainOwnerProfileSerializer(write_only=True)
    address = accountsAdminMainOwnerAddressSerializer(write_only=True)
    phone_number = serializers.IntegerField(required=True)
    email = serializers.EmailField(required=True)
    attendance_image=accountsAdminMainOwnerAttendanceImageSerializer(write_only=True)

    location_id=serializers.IntegerField(required=True)
    project_id=serializers.IntegerField(required=True)
    assign_users_ids=serializers.ListField(child=serializers.IntegerField(), required=True)


    def validate(self, data):
        phone=data.get('phone_number')
        """
        Check that the phone number is a 10-digit integer.
        """
        if not isinstance(phone, int):
            raise serializers.ValidationError({"message":"Phone number must be an integer.","status": status.HTTP_400_BAD_REQUEST})
        if len(str(phone)) != 10:
            raise serializers.ValidationError({"message":"Phone number must be a 10-digit integer.","status": status.HTTP_400_BAD_REQUEST})


        try:
            user_location=attendanceLocationsModel.objects.get(id=data.get('location_id'))
        except:
            raise serializers.ValidationError({"message":"location Does Not Exists","status": status.HTTP_400_BAD_REQUEST})

        try:
            user_project=projectsPModel.objects.get(id=data.get('project_id'))
        except:
            raise serializers.ValidationError({"message":"Project Does Not Exists","status": status.HTTP_400_BAD_REQUEST})

        assign_users_ids = data.get('assign_users_ids')
        if assign_users_ids is not None:
            for user_id in assign_users_ids:
                try:
                    user=get_user_model().objects.get(id=user_id)
                except:
                    raise serializers.ValidationError({"message":"assign user does not Exists","status": status.HTTP_400_BAD_REQUEST})

        user_phone = get_user_model().objects.filter(phone_number=data.get('phone_number'))
        user_email = get_user_model().objects.filter(email=data.get('email'))
        if user_phone.exists():
            raise serializers.ValidationError({"message": "Main Owner already exists", "status": status.HTTP_400_BAD_REQUEST})
        if user_email.exists():
            raise serializers.ValidationError({"message": "Main Owner already exists", "status": status.HTTP_400_BAD_REQUEST})
        return data

    class Meta:
        fields = ['email','profile','address','phone_number','attendance_image','location_id','project_id','assign_users_ids']

    def create(self, validated_data):
        print(validated_data,'--------')
        phone = validated_data.get('phone_number')
        email = validated_data.get('email')
        location=validated_data.get('location_id')
        project=validated_data.get('project_id')
        address_data = validated_data.get('address')
        profile_data = validated_data.get('profile')
        attendance_data=validated_data.get('attendance_image')
        assign_users_ids=validated_data.get('assign_users_ids')
        user_project = projectsPModel.objects.get(id=project)
        user_location=attendanceLocationsModel.objects.get(id=location)
        print(user_project,user_location)

        # user create
        user = get_user_model().objects.create_Main_Owner(phone_number=phone, password=str(phone),email=email)
        if user:
            # user profile create
            try:
                user_profile = accountsUserProfileModel.objects.create(owner=user, **profile_data)
                print(user_profile, '----------user profile')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user profile not created", "status": status.HTTP_400_BAD_REQUEST})
            # user address create
            try:
                user_address = accountsUserAddressModel.objects.create(owner=user, **address_data)
                print(user_address, '----------user address')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user address not created", "status": status.HTTP_400_BAD_REQUEST})
            # user attendance image create
            try:
                user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=user,
                                                                                          **attendance_data)
                print(user_attendance_image, '----------user attendance image')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user attendance image not created", "status": status.HTTP_400_BAD_REQUEST})
            #assign user project with users
            if user_project:
                print(user_project,"user project id send")
                try:
                    user_project_assign_user=projectsPAttendanceUsersModel.objects.get(project=user_project)
                    print(user_project_assign_user,'----------------------------user assign ',user_project,'----------user project')
                except:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.create(project=user_project)
                    print("new project created ")
                try:
                    for user_id in assign_users_ids:
                        user_assign = get_user_model().objects.get(id=user_id)
                        user_project_assign_user.owner.add(user_assign.id)
                        user_project_assign_user.save()
                        print("assigned now",user_assign)
                except:
                    user.delete()
                    user_project_assign_user.delete()
                    raise serializers.ValidationError({"message":"assign user not created","status": status.HTTP_400_BAD_REQUEST})
            # assign user location
            if user_location:
                try:
                    user_attendance=attendanceUserAttendanceLocationsModel.objects.create(owner=user,location=user_location)
                    print("assign user location ",user_attendance)
                except:
                    user.delete()
                    raise serializers.ValidationError({"message":"attendance location not created", "status": status.HTTP_400_BAD_REQUEST})

        else:
            raise serializers.ValidationError(
                        {"message": "Main Owner not created ", "status": status.HTTP_400_BAD_REQUEST})

        return validated_data

# # </editor-fold>

# <editor-fold desc="Serializer For New Employee Create">
class accountAdminEmployeeProfileSerializer(serializers.ModelSerializer):
    """
    optional
    date_of_birth,gender,image

    """

    class Meta:
        model = accountsUserProfileModel
        exclude = ['date_created', 'owner']


class accountsAdminEmployeeAddressSerializer(serializers.ModelSerializer):
    """
    optional
        pincode,address_proof
    """
    class Meta:
        model = accountsUserAddressModel
        exclude = ['owner', ]
class accountsAdminEmployeeAttendanceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = attendanceUserAttendanceImageModel
        exclude = ['owner', ]


class accountsAdminEmployeeSerializer(serializers.Serializer):
    """
    first_name,last_name,id_Proof, address,city,state,country,phone_number,attendance_image

    """
    profile = accountAdminEmployeeProfileSerializer(write_only=True)
    address = accountsAdminEmployeeAddressSerializer(write_only=True)
    attendance_image=accountsAdminEmployeeAttendanceImageSerializer(write_only=True)
    phone_number = serializers.IntegerField(required=True)
    email = serializers.EmailField(required=True)

    location_id=serializers.IntegerField(required=True)
    project_id=serializers.IntegerField(required=True)
    assign_users_ids=serializers.ListField(child=serializers.IntegerField(), required=True)

    def validate(self, data):
        phone = data.get('phone_number')
        """
        Check that the phone number is a 10-digit integer.
        """
        if not isinstance(phone, int):
            raise serializers.ValidationError(
                {"message": "Phone number must be an integer.", "status": status.HTTP_400_BAD_REQUEST})
        if len(str(phone)) != 10:
            raise serializers.ValidationError(
                {"message": "Phone number must be a 10-digit integer.", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_location = attendanceLocationsModel.objects.get(id=data.get('location_id'))
        except:
            raise serializers.ValidationError(
                {"message": "location Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_project = projectsPModel.objects.get(id=data.get('project_id'))
        except:
            raise serializers.ValidationError(
                {"message": "Project Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        assign_users_ids = data.get('assign_users_ids')
        if assign_users_ids is not None:
            for user_id in assign_users_ids:
                try:
                    user = get_user_model().objects.get(id=user_id)
                except:
                    raise serializers.ValidationError(
                        {"message": "assign user does not Exists", "status": status.HTTP_400_BAD_REQUEST})

        user_phone = get_user_model().objects.filter(phone_number=data.get('phone_number'))
        user_email = get_user_model().objects.filter(email=data.get('email'))
        if user_phone.exists():
            raise serializers.ValidationError(
                {"message": "Employee already exists", "status": status.HTTP_400_BAD_REQUEST})
        if user_email.exists():
            raise serializers.ValidationError(
                {"message": "Employee already exists", "status": status.HTTP_400_BAD_REQUEST})
        return data

    class Meta:
        fields = ['email', 'profile', 'address', 'phone_number', 'attendance_image', 'location_id', 'project_id',
                  'assign_users_ids']

    def create(self, validated_data):
        print(validated_data, '--------')
        phone = validated_data.get('phone_number')
        email = validated_data.get('email')
        location = validated_data.get('location_id')
        project = validated_data.get('project_id')
        address_data = validated_data.get('address')
        profile_data = validated_data.get('profile')
        attendance_data = validated_data.get('attendance_image')
        assign_users_ids = validated_data.get('assign_users_ids')
        user_project = projectsPModel.objects.get(id=project)
        user_location = attendanceLocationsModel.objects.get(id=location)
        print(user_project, user_location)

        # user create
        user = get_user_model().objects.create_employee(phone_number=phone, password=str(phone), email=email)
        if user:
            # user profile create
            try:
                user_profile = accountsUserProfileModel.objects.create(owner=user, **profile_data)
                print(user_profile, '----------user profile')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user profile not created", "status": status.HTTP_400_BAD_REQUEST})
            # user address create
            try:
                user_address = accountsUserAddressModel.objects.create(owner=user, **address_data)
                print(user_address, '----------user address')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user address not created", "status": status.HTTP_400_BAD_REQUEST})
            # user attendance image create
            try:
                user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=user,
                                                                                          **attendance_data)
                print(user_attendance_image, '----------user attendance image')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user attendance image not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user project with users
            if user_project:
                print(user_project, "user project id send")
                try:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.get(project=user_project)
                    print(user_project_assign_user, '----------------------------user assign ', user_project,
                          '----------user project')
                except:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.create(project=user_project)
                    print("new project created ")
                try:
                    for user_id in assign_users_ids:
                        user_assign = get_user_model().objects.get(id=user_id)
                        user_project_assign_user.owner.add(user_assign.id)
                        user_project_assign_user.save()
                        print("assigned now", user_assign)
                except:
                    user.delete()
                    user_project_assign_user.delete()
                    raise serializers.ValidationError(
                        {"message": "assign user not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user location
            if user_location:
                try:
                    user_attendance = attendanceUserAttendanceLocationsModel.objects.create(owner=user,
                                                                                            location=user_location)
                    print("assign user location ", user_attendance)
                except:
                    user.delete()
                    raise serializers.ValidationError(
                        {"message": "attendance location not created", "status": status.HTTP_400_BAD_REQUEST})

        else:
            raise serializers.ValidationError(
                {"message": "Employee not created ", "status": status.HTTP_400_BAD_REQUEST})

        return validated_data


# </editor-fold>

# <editor-fold desc="Serializer For New Supervisor Create">
class accountAdminSupervisorProfileSerializer(serializers.ModelSerializer):
    """
    optional
    date_of_birth,gender,image

    """

    class Meta:
        model = accountsUserProfileModel
        exclude = ['date_created', 'owner']


class accountsAdminSupervisorAddressSerializer(serializers.ModelSerializer):
    """
    optional
        pincode,address_proof
    """
    class Meta:
        model = accountsUserAddressModel
        exclude = ['owner', ]
class accountsAdminSupervisorAttendanceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = attendanceUserAttendanceImageModel
        exclude = ['owner', ]


class accountsAdminSupervisorSerializer(serializers.Serializer):
    """
    first_name,last_name,id_Proof, address,city,state,country,phone_number,attendance_image

    """
    profile = accountAdminSupervisorProfileSerializer(write_only=True)
    address = accountsAdminSupervisorAddressSerializer(write_only=True)
    attendance_image=accountsAdminSupervisorAttendanceImageSerializer(write_only=True)
    phone_number = serializers.IntegerField(required=True)
    email = serializers.EmailField(required=True)

    location_id=serializers.IntegerField(required=True)
    project_id=serializers.IntegerField(required=True)
    assign_users_ids=serializers.ListField(child=serializers.IntegerField(), required=True)


    def validate(self, data):
        phone = data.get('phone_number')
        """
        Check that the phone number is a 10-digit integer.
        """
        if not isinstance(phone, int):
            raise serializers.ValidationError(
                {"message": "Phone number must be an integer.", "status": status.HTTP_400_BAD_REQUEST})
        if len(str(phone)) != 10:
            raise serializers.ValidationError(
                {"message": "Phone number must be a 10-digit integer.", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_location = attendanceLocationsModel.objects.get(id=data.get('location_id'))
        except:
            raise serializers.ValidationError(
                {"message": "location Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_project = projectsPModel.objects.get(id=data.get('project_id'))
        except:
            raise serializers.ValidationError(
                {"message": "Project Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        assign_users_ids = data.get('assign_users_ids')
        if assign_users_ids is not None:
            for user_id in assign_users_ids:
                try:
                    user = get_user_model().objects.get(id=user_id)
                except:
                    raise serializers.ValidationError(
                        {"message": "assign user does not Exists", "status": status.HTTP_400_BAD_REQUEST})

        user_phone = get_user_model().objects.filter(phone_number=data.get('phone_number'))
        user_email = get_user_model().objects.filter(email=data.get('email'))
        if user_phone.exists():
            raise serializers.ValidationError(
                {"message": "Supervisor already exists", "status": status.HTTP_400_BAD_REQUEST})
        if user_email.exists():
            raise serializers.ValidationError(
                {"message": "Supervisor already exists", "status": status.HTTP_400_BAD_REQUEST})
        return data

    class Meta:
        fields = ['email', 'profile', 'address', 'phone_number', 'attendance_image', 'location_id', 'project_id',
                  'assign_users_ids']

    def create(self, validated_data):
        print(validated_data, '--------')
        phone = validated_data.get('phone_number')
        email = validated_data.get('email')
        location = validated_data.get('location_id')
        project = validated_data.get('project_id')
        address_data = validated_data.get('address')
        profile_data = validated_data.get('profile')
        attendance_data = validated_data.get('attendance_image')
        assign_users_ids = validated_data.get('assign_users_ids')
        user_project = projectsPModel.objects.get(id=project)
        user_location = attendanceLocationsModel.objects.get(id=location)
        print(user_project, user_location)

        # user create
        user = get_user_model().objects.create_supervisor(phone_number=phone, password=str(phone), email=email)
        if user:
            # user profile create
            try:
                user_profile = accountsUserProfileModel.objects.create(owner=user, **profile_data)
                print(user_profile, '----------user profile')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user profile not created", "status": status.HTTP_400_BAD_REQUEST})
            # user address create
            try:
                user_address = accountsUserAddressModel.objects.create(owner=user, **address_data)
                print(user_address, '----------user address')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user address not created", "status": status.HTTP_400_BAD_REQUEST})
            # user attendance image create
            try:
                user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=user,
                                                                                          **attendance_data)
                print(user_attendance_image, '----------user attendance image')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user attendance image not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user project with users
            if user_project:
                print(user_project, "user project id send")
                try:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.get(project=user_project)
                    print(user_project_assign_user, '----------------------------user assign ', user_project,
                          '----------user project')
                except:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.create(project=user_project)
                    print("new project created ")
                try:
                    for user_id in assign_users_ids:
                        user_assign = get_user_model().objects.get(id=user_id)
                        user_project_assign_user.owner.add(user_assign.id)
                        user_project_assign_user.save()
                        print("assigned now", user_assign)
                except:
                    user.delete()
                    user_project_assign_user.delete()
                    raise serializers.ValidationError(
                        {"message": "assign user not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user location
            if user_location:
                try:
                    user_attendance = attendanceUserAttendanceLocationsModel.objects.create(owner=user,
                                                                                            location=user_location)
                    print("assign user location ", user_attendance)
                except:
                    user.delete()
                    raise serializers.ValidationError(
                        {"message": "attendance location not created", "status": status.HTTP_400_BAD_REQUEST})

        else:
            raise serializers.ValidationError(
                {"message": "Supervisor not created ", "status": status.HTTP_400_BAD_REQUEST})

        return validated_data



# </editor-fold>

# <editor-fold desc="Serializer For New Store manager Create">
class accountAdminStoreManagerProfileSerializer(serializers.ModelSerializer):
    """
    optional
    date_of_birth,gender,image

    """

    class Meta:
        model = accountsUserProfileModel
        exclude = ['date_created', 'owner']


class accountsAdminStoreManagerAddressSerializer(serializers.ModelSerializer):
    """
    optional
        pincode,address_proof
    """
    class Meta:
        model = accountsUserAddressModel
        exclude = ['owner', ]
class accountsAdminStoreManagerAttendanceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = attendanceUserAttendanceImageModel
        exclude = ['owner', ]


class accountsAdminStoreManagerSerializer(serializers.Serializer):
    """
    first_name,last_name,id_Proof, address,city,state,country,phone_number,attendance_image

    """
    profile = accountAdminStoreManagerProfileSerializer(write_only=True)
    address = accountsAdminStoreManagerAddressSerializer(write_only=True)
    attendance_image=accountsAdminStoreManagerAttendanceImageSerializer(write_only=True)
    phone_number = serializers.IntegerField(required=True)
    email=serializers.EmailField(required=True)

    location_id=serializers.IntegerField(required=True)
    project_id=serializers.IntegerField(required=True)
    assign_users_ids=serializers.ListField(child=serializers.IntegerField(), required=True)


    def validate(self, data):
        phone = data.get('phone_number')
        """
        Check that the phone number is a 10-digit integer.
        """
        if not isinstance(phone, int):
            raise serializers.ValidationError(
                {"message": "Phone number must be an integer.", "status": status.HTTP_400_BAD_REQUEST})
        if len(str(phone)) != 10:
            raise serializers.ValidationError(
                {"message": "Phone number must be a 10-digit integer.", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_location = attendanceLocationsModel.objects.get(id=data.get('location_id'))
        except:
            raise serializers.ValidationError(
                {"message": "location Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_project = projectsPModel.objects.get(id=data.get('project_id'))
        except:
            raise serializers.ValidationError(
                {"message": "Project Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        assign_users_ids = data.get('assign_users_ids')
        if assign_users_ids is not None:
            for user_id in assign_users_ids:
                try:
                    user = get_user_model().objects.get(id=user_id)
                except:
                    raise serializers.ValidationError(
                        {"message": "assign user does not Exists", "status": status.HTTP_400_BAD_REQUEST})

        user_phone = get_user_model().objects.filter(phone_number=data.get('phone_number'))
        user_email = get_user_model().objects.filter(email=data.get('email'))
        if user_phone.exists():
            raise serializers.ValidationError(
                {"message": "Store manager already exists", "status": status.HTTP_400_BAD_REQUEST})
        if user_email.exists():
            raise serializers.ValidationError(
                {"message": "Store manager already exists", "status": status.HTTP_400_BAD_REQUEST})
        return data

    class Meta:
        fields = ['email', 'profile', 'address', 'phone_number', 'attendance_image', 'location_id', 'project_id',
                  'assign_users_ids']

    def create(self, validated_data):
        print(validated_data, '--------')
        phone = validated_data.get('phone_number')
        email = validated_data.get('email')
        location = validated_data.get('location_id')
        project = validated_data.get('project_id')
        address_data = validated_data.get('address')
        profile_data = validated_data.get('profile')
        attendance_data = validated_data.get('attendance_image')
        assign_users_ids = validated_data.get('assign_users_ids')
        user_project = projectsPModel.objects.get(id=project)
        user_location = attendanceLocationsModel.objects.get(id=location)
        print(user_project, user_location)

        # user create
        user = get_user_model().objects.create_store_manager(phone_number=phone, password=str(phone), email=email)
        if user:
            # user profile create
            try:
                user_profile = accountsUserProfileModel.objects.create(owner=user, **profile_data)
                print(user_profile, '----------user profile')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user profile not created", "status": status.HTTP_400_BAD_REQUEST})
            # user address create
            try:
                user_address = accountsUserAddressModel.objects.create(owner=user, **address_data)
                print(user_address, '----------user address')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user address not created", "status": status.HTTP_400_BAD_REQUEST})
            # user attendance image create
            try:
                user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=user,
                                                                                          **attendance_data)
                print(user_attendance_image, '----------user attendance image')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user attendance image not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user project with users
            if user_project:
                print(user_project, "user project id send")
                try:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.get(project=user_project)
                    print(user_project_assign_user, '----------------------------user assign ', user_project,
                          '----------user project')
                except:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.create(project=user_project)
                    print("new project created ")
                try:
                    for user_id in assign_users_ids:
                        user_assign = get_user_model().objects.get(id=user_id)
                        user_project_assign_user.owner.add(user_assign.id)
                        user_project_assign_user.save()
                        print("assigned now", user_assign)
                except:
                    user.delete()
                    user_project_assign_user.delete()
                    raise serializers.ValidationError(
                        {"message": "assign user not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user location
            if user_location:
                try:
                    user_attendance = attendanceUserAttendanceLocationsModel.objects.create(owner=user,
                                                                                            location=user_location)
                    print("assign user location ", user_attendance)
                except:
                    user.delete()
                    raise serializers.ValidationError(
                        {"message": "attendance location not created", "status": status.HTTP_400_BAD_REQUEST})

        else:
            raise serializers.ValidationError(
                {"message": "Store manager not created ", "status": status.HTTP_400_BAD_REQUEST})

        return validated_data



# </editor-fold>

# <editor-fold desc="Serializer For New Garage manager Create">
class accountAdminGaragemanagerProfileSerializer(serializers.ModelSerializer):
    """
    optional
    date_of_birth,gender,image

    """

    class Meta:
        model = accountsUserProfileModel
        exclude = ['date_created', 'owner']


class accountsAdminGaragemanagerAddressSerializer(serializers.ModelSerializer):
    """
    optional
        pincode,address_proof
    """
    class Meta:
        model = accountsUserAddressModel
        exclude = ['owner', ]
class accountsAdminGaragemanagerAttendanceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = attendanceUserAttendanceImageModel
        exclude = ['owner', ]


class accountsAdminGaragemanagerSerializer(serializers.Serializer):
    """
    first_name,last_name,id_Proof, address,city,state,country,phone_number,attendance_image

    """
    profile = accountAdminGaragemanagerProfileSerializer(write_only=True)
    address = accountsAdminGaragemanagerAddressSerializer(write_only=True)
    attendance_image=accountsAdminGaragemanagerAttendanceImageSerializer(write_only=True)
    phone_number = serializers.IntegerField(required=True)
    email=serializers.EmailField(required=True)

    location_id=serializers.IntegerField(required=True)
    project_id=serializers.IntegerField(required=True)
    assign_users_ids=serializers.ListField(child=serializers.IntegerField(), required=True)


    def validate(self, data):
        phone = data.get('phone_number')
        """
        Check that the phone number is a 10-digit integer.
        """
        if not isinstance(phone, int):
            raise serializers.ValidationError(
                {"message": "Phone number must be an integer.", "status": status.HTTP_400_BAD_REQUEST})
        if len(str(phone)) != 10:
            raise serializers.ValidationError(
                {"message": "Phone number must be a 10-digit integer.", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_location = attendanceLocationsModel.objects.get(id=data.get('location_id'))
        except:
            raise serializers.ValidationError(
                {"message": "location Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_project = projectsPModel.objects.get(id=data.get('project_id'))
        except:
            raise serializers.ValidationError(
                {"message": "Project Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        assign_users_ids = data.get('assign_users_ids')
        if assign_users_ids is not None:
            for user_id in assign_users_ids:
                try:
                    user = get_user_model().objects.get(id=user_id)
                except:
                    raise serializers.ValidationError(
                        {"message": "assign user does not Exists", "status": status.HTTP_400_BAD_REQUEST})

        user_phone = get_user_model().objects.filter(phone_number=data.get('phone_number'))
        user_email = get_user_model().objects.filter(email=data.get('email'))
        if user_phone.exists():
            raise serializers.ValidationError(
                {"message": "Garage manager already exists", "status": status.HTTP_400_BAD_REQUEST})
        if user_email.exists():
            raise serializers.ValidationError(
                {"message": "Garage manager already exists", "status": status.HTTP_400_BAD_REQUEST})
        return data

    class Meta:
        fields = ['email', 'profile', 'address', 'phone_number', 'attendance_image', 'location_id', 'project_id',
                  'assign_users_ids']

    def create(self, validated_data):
        print(validated_data, '--------')
        phone = validated_data.get('phone_number')
        email = validated_data.get('email')
        location = validated_data.get('location_id')
        project = validated_data.get('project_id')
        address_data = validated_data.get('address')
        profile_data = validated_data.get('profile')
        attendance_data = validated_data.get('attendance_image')
        assign_users_ids = validated_data.get('assign_users_ids')
        user_project = projectsPModel.objects.get(id=project)
        user_location = attendanceLocationsModel.objects.get(id=location)
        print(user_project, user_location)

        # user create
        user = get_user_model().objects.create_gaurage_manager(phone_number=phone, password=str(phone), email=email)
        if user:
            # user profile create
            try:
                user_profile = accountsUserProfileModel.objects.create(owner=user, **profile_data)
                print(user_profile, '----------user profile')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user profile not created", "status": status.HTTP_400_BAD_REQUEST})
            # user address create
            try:
                user_address = accountsUserAddressModel.objects.create(owner=user, **address_data)
                print(user_address, '----------user address')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user address not created", "status": status.HTTP_400_BAD_REQUEST})
            # user attendance image create
            try:
                user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=user,
                                                                                          **attendance_data)
                print(user_attendance_image, '----------user attendance image')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user attendance image not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user project with users
            if user_project:
                print(user_project, "user project id send")
                try:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.get(project=user_project)
                    print(user_project_assign_user, '----------------------------user assign ', user_project,
                          '----------user project')
                except:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.create(project=user_project)
                    print("new project created ")
                try:
                    for user_id in assign_users_ids:
                        user_assign = get_user_model().objects.get(id=user_id)
                        user_project_assign_user.owner.add(user_assign.id)
                        user_project_assign_user.save()
                        print("assigned now", user_assign)
                except:
                    user.delete()
                    user_project_assign_user.delete()
                    raise serializers.ValidationError(
                        {"message": "assign user not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user location
            if user_location:
                try:
                    user_attendance = attendanceUserAttendanceLocationsModel.objects.create(owner=user,
                                                                                            location=user_location)
                    print("assign user location ", user_attendance)
                except:
                    user.delete()
                    raise serializers.ValidationError(
                        {"message": "attendance location not created", "status": status.HTTP_400_BAD_REQUEST})

        else:
            raise serializers.ValidationError(
                {"message": "garage manager not created ", "status": status.HTTP_400_BAD_REQUEST})

        return validated_data



# </editor-fold>

# <editor-fold desc="Serializer For New Project Manager Create">
class accountAdminProjectManagerProfileSerializer(serializers.ModelSerializer):
    """
    optional
    date_of_birth,gender,image

    """

    class Meta:
        model = accountsUserProfileModel
        exclude = ['date_created', 'owner']


class accountsAdminProjectManagerAddressSerializer(serializers.ModelSerializer):
    """
    optional
        pincode,address_proof
    """
    class Meta:
        model = accountsUserAddressModel
        exclude = ['owner', ]
class accountsAdminProjectManagerAttendanceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = attendanceUserAttendanceImageModel
        exclude = ['owner', ]


class accountsAdminProjectManagerSerializer(serializers.Serializer):
    """
    first_name,last_name,id_Proof, address,city,state,country,phone_number,attendance_image

    """
    profile = accountAdminProjectManagerProfileSerializer(write_only=True)
    address = accountsAdminProjectManagerAddressSerializer(write_only=True)
    attendance_image=accountsAdminProjectManagerAttendanceImageSerializer(write_only=True)
    phone_number = serializers.IntegerField(required=True)
    email=serializers.EmailField(required=True)

    location_id=serializers.IntegerField(required=True)
    project_id=serializers.IntegerField(required=True)
    assign_users_ids=serializers.ListField(child=serializers.IntegerField(), required=True)



    def validate(self, data):
        phone = data.get('phone_number')
        """
        Check that the phone number is a 10-digit integer.
        """
        if not isinstance(phone, int):
            raise serializers.ValidationError(
                {"message": "Phone number must be an integer.", "status": status.HTTP_400_BAD_REQUEST})
        if len(str(phone)) != 10:
            raise serializers.ValidationError(
                {"message": "Phone number must be a 10-digit integer.", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_location = attendanceLocationsModel.objects.get(id=data.get('location_id'))
        except:
            raise serializers.ValidationError(
                {"message": "location Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_project = projectsPModel.objects.get(id=data.get('project_id'))
        except:
            raise serializers.ValidationError(
                {"message": "Project Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        assign_users_ids = data.get('assign_users_ids')
        if assign_users_ids is not None:
            for user_id in assign_users_ids:
                try:
                    user = get_user_model().objects.get(id=user_id)
                except:
                    raise serializers.ValidationError(
                        {"message": "assign user does not Exists", "status": status.HTTP_400_BAD_REQUEST})

        user_phone = get_user_model().objects.filter(phone_number=data.get('phone_number'))
        user_email = get_user_model().objects.filter(email=data.get('email'))
        if user_phone.exists():
            raise serializers.ValidationError(
                {"message": "Project manager already exists", "status": status.HTTP_400_BAD_REQUEST})
        if user_email.exists():
            raise serializers.ValidationError(
                {"message": "Project manager already exists", "status": status.HTTP_400_BAD_REQUEST})
        return data

    class Meta:
        fields = ['email', 'profile', 'address', 'phone_number', 'attendance_image', 'location_id', 'project_id',
                  'assign_users_ids']

    def create(self, validated_data):
        print(validated_data, '--------')
        phone = validated_data.get('phone_number')
        email = validated_data.get('email')
        location = validated_data.get('location_id')
        project = validated_data.get('project_id')
        address_data = validated_data.get('address')
        profile_data = validated_data.get('profile')
        attendance_data = validated_data.get('attendance_image')
        assign_users_ids = validated_data.get('assign_users_ids')
        user_project = projectsPModel.objects.get(id=project)
        user_location = attendanceLocationsModel.objects.get(id=location)
        print(user_project, user_location)

        # user create
        user = get_user_model().objects.create_project_manager(phone_number=phone, password=str(phone), email=email)
        if user:
            # user profile create
            try:
                user_profile = accountsUserProfileModel.objects.create(owner=user, **profile_data)
                print(user_profile, '----------user profile')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user profile not created", "status": status.HTTP_400_BAD_REQUEST})
            # user address create
            try:
                user_address = accountsUserAddressModel.objects.create(owner=user, **address_data)
                print(user_address, '----------user address')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user address not created", "status": status.HTTP_400_BAD_REQUEST})
            # user attendance image create
            try:
                user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=user,
                                                                                          **attendance_data)
                print(user_attendance_image, '----------user attendance image')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user attendance image not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user project with users
            if user_project:
                print(user_project, "user project id send")
                try:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.get(project=user_project)
                    print(user_project_assign_user, '----------------------------user assign ', user_project,
                          '----------user project')
                except:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.create(project=user_project)
                    print("new project created ")
                try:
                    for user_id in assign_users_ids:
                        user_assign = get_user_model().objects.get(id=user_id)
                        user_project_assign_user.owner.add(user_assign.id)
                        user_project_assign_user.save()
                        print("assigned now", user_assign)
                except:
                    user.delete()
                    user_project_assign_user.delete()
                    raise serializers.ValidationError(
                        {"message": "assign user not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user location
            if user_location:
                try:
                    user_attendance = attendanceUserAttendanceLocationsModel.objects.create(owner=user,
                                                                                            location=user_location)
                    print("assign user location ", user_attendance)
                except:
                    user.delete()
                    raise serializers.ValidationError(
                        {"message": "attendance location not created", "status": status.HTTP_400_BAD_REQUEST})

        else:
            raise serializers.ValidationError(
                {"message": "Project Manager not created ", "status": status.HTTP_400_BAD_REQUEST})

        return validated_data


# </editor-fold>

# <editor-fold desc="Serializer For New Project Coordinator Create">
class accountAdminProjectCoordinatorProfileSerializer(serializers.ModelSerializer):
    """
    optional
    date_of_birth,gender,image

    """
    class Meta:
        model = accountsUserProfileModel
        exclude = ['date_created', 'owner']


class accountsAdminProjectCoordinatorAddressSerializer(serializers.ModelSerializer):
    """
    optional
        pincode,address_proof
    """
    class Meta:
        model = accountsUserAddressModel
        exclude = ['owner', ]

class accountsAdminProjectCoordinatorAttendanceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = attendanceUserAttendanceImageModel
        exclude = ['owner', ]


class accountsAdminProjectCoordinatorSerializer(serializers.Serializer):
    profile = accountAdminProjectManagerProfileSerializer(write_only=True)
    address = accountsAdminProjectManagerAddressSerializer(write_only=True)
    phone_number = serializers.IntegerField(required=True)
    attendance_image=accountsAdminProjectCoordinatorAttendanceImageSerializer(write_only=True)
    email=serializers.EmailField(required=True)

    location_id=serializers.IntegerField(required=True)
    project_id=serializers.IntegerField(required=True)
    assign_users_ids=serializers.ListField(child=serializers.IntegerField(), required=True)



    def validate(self, data):
        phone = data.get('phone_number')
        """
        Check that the phone number is a 10-digit integer.
        """
        if not isinstance(phone, int):
            raise serializers.ValidationError(
                {"message": "Phone number must be an integer.", "status": status.HTTP_400_BAD_REQUEST})
        if len(str(phone)) != 10:
            raise serializers.ValidationError(
                {"message": "Phone number must be a 10-digit integer.", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_location = attendanceLocationsModel.objects.get(id=data.get('location_id'))
        except:
            raise serializers.ValidationError(
                {"message": "location Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_project = projectsPModel.objects.get(id=data.get('project_id'))
        except:
            raise serializers.ValidationError(
                {"message": "Project Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        assign_users_ids = data.get('assign_users_ids')
        if assign_users_ids is not None:
            for user_id in assign_users_ids:
                try:
                    user = get_user_model().objects.get(id=user_id)
                except:
                    raise serializers.ValidationError(
                        {"message": "assign user does not Exists", "status": status.HTTP_400_BAD_REQUEST})

        user_phone = get_user_model().objects.filter(phone_number=data.get('phone_number'))
        user_email = get_user_model().objects.filter(email=data.get('email'))
        if user_phone.exists():
            raise serializers.ValidationError(
                {"message": "Project Coordinator already exists", "status": status.HTTP_400_BAD_REQUEST})
        if user_email.exists():
            raise serializers.ValidationError(
                {"message": "Project Coordinator already exists", "status": status.HTTP_400_BAD_REQUEST})
        return data

    class Meta:
        fields = ['email', 'profile', 'address', 'phone_number', 'attendance_image', 'location_id', 'project_id',
                  'assign_users_ids']

    def create(self, validated_data):
        print(validated_data, '--------')
        phone = validated_data.get('phone_number')
        email = validated_data.get('email')
        location = validated_data.get('location_id')
        project = validated_data.get('project_id')
        address_data = validated_data.get('address')
        profile_data = validated_data.get('profile')
        attendance_data = validated_data.get('attendance_image')
        assign_users_ids = validated_data.get('assign_users_ids')
        user_project = projectsPModel.objects.get(id=project)
        user_location = attendanceLocationsModel.objects.get(id=location)
        print(user_project, user_location)

        # user create
        user = get_user_model().objects.create_project_coordinator(phone_number=phone, password=str(phone), email=email)
        if user:
            # user profile create
            try:
                user_profile = accountsUserProfileModel.objects.create(owner=user, **profile_data)
                print(user_profile, '----------user profile')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user profile not created", "status": status.HTTP_400_BAD_REQUEST})
            # user address create
            try:
                user_address = accountsUserAddressModel.objects.create(owner=user, **address_data)
                print(user_address, '----------user address')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user address not created", "status": status.HTTP_400_BAD_REQUEST})
            # user attendance image create
            try:
                user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=user,
                                                                                          **attendance_data)
                print(user_attendance_image, '----------user attendance image')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user attendance image not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user project with users
            if user_project:
                print(user_project, "user project id send")
                try:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.get(project=user_project)
                    print(user_project_assign_user, '----------------------------user assign ', user_project,
                          '----------user project')
                except:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.create(project=user_project)
                    print("new project created ")
                try:
                    for user_id in assign_users_ids:
                        user_assign = get_user_model().objects.get(id=user_id)
                        user_project_assign_user.owner.add(user_assign.id)
                        user_project_assign_user.save()
                        print("assigned now", user_assign)
                except:
                    user.delete()
                    user_project_assign_user.delete()
                    raise serializers.ValidationError(
                        {"message": "assign user not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user location
            if user_location:
                try:
                    user_attendance = attendanceUserAttendanceLocationsModel.objects.create(owner=user,
                                                                                            location=user_location)
                    print("assign user location ", user_attendance)
                except:
                    user.delete()
                    raise serializers.ValidationError(
                        {"message": "attendance location not created", "status": status.HTTP_400_BAD_REQUEST})

        else:
            raise serializers.ValidationError(
                {"message": "project coordinator not created ", "status": status.HTTP_400_BAD_REQUEST})

        return validated_data

# # </editor-fold>

# # <editor-fold desc="Serializer For New Head Officer Create">
class accountAdminHeadOfficeProfileSerializer(serializers.ModelSerializer):
    """
    optional
    date_of_birth,gender,image

    """
    class Meta:
        model = accountsUserProfileModel
        exclude = ['date_created', 'owner']


class accountsAdminHeadOfficeAddressSerializer(serializers.ModelSerializer):
    """
    optional
        pincode,address_proof
    """
    class Meta:
        model = accountsUserAddressModel
        exclude = ['owner', ]


class accountsAdminHeadOfficeAttendanceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = attendanceUserAttendanceImageModel
        exclude = ['owner', ]

class accountsAdminHeadOfficeSerializer(serializers.Serializer):
    profile = accountAdminHeadOfficeProfileSerializer(write_only=True)
    address = accountsAdminHeadOfficeAddressSerializer(write_only=True)
    phone_number = serializers.IntegerField(required=True)
    attendance_image=accountsAdminHeadOfficeAttendanceImageSerializer(write_only=True)
    email=serializers.EmailField(required=True)
    location_id=serializers.IntegerField(required=True)
    project_id=serializers.IntegerField(required=True)
    assign_users_ids=serializers.ListField(child=serializers.IntegerField(), required=True)




    def validate(self, data):
        phone = data.get('phone_number')
        """
        Check that the phone number is a 10-digit integer.
        """
        if not isinstance(phone, int):
            raise serializers.ValidationError(
                {"message": "Phone number must be an integer.", "status": status.HTTP_400_BAD_REQUEST})
        if len(str(phone)) != 10:
            raise serializers.ValidationError(
                {"message": "Phone number must be a 10-digit integer.", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_location = attendanceLocationsModel.objects.get(id=data.get('location_id'))
        except:
            raise serializers.ValidationError(
                {"message": "location Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        try:
            user_project = projectsPModel.objects.get(id=data.get('project_id'))
        except:
            raise serializers.ValidationError(
                {"message": "Project Does Not Exists", "status": status.HTTP_400_BAD_REQUEST})

        assign_users_ids = data.get('assign_users_ids')
        if assign_users_ids is not None:
            for user_id in assign_users_ids:
                try:
                    user = get_user_model().objects.get(id=user_id)
                except:
                    raise serializers.ValidationError(
                        {"message": "assign user does not Exists", "status": status.HTTP_400_BAD_REQUEST})

        user_phone = get_user_model().objects.filter(phone_number=data.get('phone_number'))
        user_email = get_user_model().objects.filter(email=data.get('email'))
        if user_phone.exists():
            raise serializers.ValidationError(
                {"message": "head office already exists", "status": status.HTTP_400_BAD_REQUEST})
        if user_email.exists():
            raise serializers.ValidationError(
                {"message": "head office already exists", "status": status.HTTP_400_BAD_REQUEST})
        return data

    class Meta:
        fields = ['email', 'profile', 'address', 'phone_number', 'attendance_image', 'location_id', 'project_id',
                  'assign_users_ids']

    def create(self, validated_data):
        print(validated_data, '--------')
        phone = validated_data.get('phone_number')
        email = validated_data.get('email')
        location = validated_data.get('location_id')
        project = validated_data.get('project_id')
        address_data = validated_data.get('address')
        profile_data = validated_data.get('profile')
        attendance_data = validated_data.get('attendance_image')
        assign_users_ids = validated_data.get('assign_users_ids')
        user_project = projectsPModel.objects.get(id=project)
        user_location = attendanceLocationsModel.objects.get(id=location)
        print(user_project, user_location)

        # user create
        user = get_user_model().objects.create_headoffice(phone_number=phone, password=str(phone), email=email)
        if user:
            # user profile create
            try:
                user_profile = accountsUserProfileModel.objects.create(owner=user, **profile_data)
                print(user_profile, '----------user profile')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user profile not created", "status": status.HTTP_400_BAD_REQUEST})
            # user address create
            try:
                user_address = accountsUserAddressModel.objects.create(owner=user, **address_data)
                print(user_address, '----------user address')
            except:
                user.delete()
                raise serializers.ValidationError({"message": "user address not created", "status": status.HTTP_400_BAD_REQUEST})
            # user attendance image create
            try:
                user_attendance_image = attendanceUserAttendanceImageModel.objects.create(owner=user,**attendance_data)
                print(user_attendance_image, '----------user attendance image')
            except:
                user.delete()
                raise serializers.ValidationError(
                    {"message": "user attendance image not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user project with users
            if user_project:
                print(user_project, "user project id send")
                try:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.get(project=user_project)
                    print(user_project_assign_user, '----------------------------user assign ', user_project,
                          '----------user project')
                except:
                    user_project_assign_user = projectsPAttendanceUsersModel.objects.create(project=user_project)
                    print("new project created ")
                try:
                    for user_id in assign_users_ids:
                        user_assign = get_user_model().objects.get(id=user_id)
                        user_project_assign_user.owner.add(user_assign.id)
                        user_project_assign_user.save()
                        print("assigned now", user_assign)
                except:
                    user.delete()
                    user_project_assign_user.delete()
                    raise serializers.ValidationError(
                        {"message": "assign user not created", "status": status.HTTP_400_BAD_REQUEST})
            # assign user location
            if user_location:
                try:
                    user_attendance = attendanceUserAttendanceLocationsModel.objects.create(owner=user,
                                                                                            location=user_location)
                    print("assign user location ", user_attendance)
                except:
                    user.delete()
                    raise serializers.ValidationError(
                        {"message": "attendance location not created", "status": status.HTTP_400_BAD_REQUEST})

        else:
            raise serializers.ValidationError(
                {"message": "head office not created ", "status": status.HTTP_400_BAD_REQUEST})

        return validated_data

# # </editor-fold>

# new add
##ALL USERS WITH PROFILES
class usersProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = "__all__"

class userModelGetSerializers(serializers.ModelSerializer):
    owner_profile = serializers.SerializerMethodField(read_only=True)

    def get_owner_profile(self,obj):
        try:
            owner_profile = usersProfileSerializer(obj.accountsUserProfileModel_user_profile).data
            try:
                owner_profile["image"] = obj.accountsUserProfileModel_user_profile.image.url
            except:
                owner_profile["image"] = ""
        except:
            owner_profile = {}
        return owner_profile

    class Meta:
        model = get_user_model()
        fields = ["id","phone_number","employee_id","email","slug","owner_profile",]


# <editor-fold desc="Login User attendance">
class accountsAdminLoginUserAttendanceStatsSerializers(serializers.ModelSerializer):
    over_all_attendance_stats = serializers.SerializerMethodField(read_only=True)

    def get_over_all_attendance_stats(self,obj):
        over_all_attendance_stats = {}
        today_date = datetime.today().date()
        attendance_main = obj.attendanceUserAttendanceMainModel_owner.all()
        approved_attendance = obj.attendanceUserAttendanceMainModel_owner.filter(approved="APPROVED")
        unapproved_attendance = obj.attendanceUserAttendanceMainModel_owner.filter(approved="UNAPPROVED")
        try:
            start_date = attendance_main.last().created_at.date()
        except:
            start_date = today_date
        over_all_attendance = len(attendance_main)
        over_all_attendance_stats["total_attendance"] = over_all_attendance
        over_all_attendance_stats["total_approved_attendance"] = len(approved_attendance)
        over_all_attendance_stats["total_unapproved_attendance"] = len(unapproved_attendance)
        over_all_attendance_stats["total_days"] = (today_date - start_date).days
        over_all_attendance_stats["total_presents"] = over_all_attendance_stats["total_approved_attendance"]
        over_all_attendance_stats["total_absents"] = over_all_attendance_stats["total_days"] - over_all_attendance_stats["total_approved_attendance"]
        return over_all_attendance_stats

    class Meta:
        model = get_user_model()
        fields = ["id","phone_number","employee_id","email","slug","over_all_attendance_stats",]
# </editor-fold>

# <editor-fold desc="Serializer For User phone number and email update ">
class accountsAdminUserDetailUpdateSerializer(serializers.Serializer):
    phone=serializers.IntegerField(write_only=True)
    email_address=serializers.CharField(write_only=True)

    def validate(self, data):
        print("data================",data)

        phone_number = data.get('phone')
        email = data.get('email_address')
        print(email,'-----------email get')
        if not re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email):
            raise serializers.ValidationError({"message": "Invalid email address", "status": status.HTTP_400_BAD_REQUEST})
        """
        Check that the phone number is a 10-digit integer.
        """
        if not isinstance(phone_number, int):
            raise serializers.ValidationError(
                {"message": "Phone number must be an integer.", "status": status.HTTP_400_BAD_REQUEST})
        if len(str(phone_number)) != 10:
            raise serializers.ValidationError(
                {"message": "Phone number must be a 10-digit integer.", "status": status.HTTP_400_BAD_REQUEST})

        # Check email validity
        return data

    class Meta:
        fields = ["phone", "email_address", ]


    def update(self, instance, validated_data):
        # Check if another user already has the same phone number or email
        phone_number = validated_data.get('phone')
        email = validated_data.get('email_address')

        if get_user_model().objects.filter(~Q(id=instance.id),Q(email=email)).exists():
            raise serializers.ValidationError(
                {"message": "email already in use.", "status": status.HTTP_400_BAD_REQUEST})
        if get_user_model().objects.filter(~Q(id=instance.id), Q(phone_number=phone_number)).exists():
            raise serializers.ValidationError(
                {"message": "Phone number already in use.", "status": status.HTTP_400_BAD_REQUEST})

        # Update the instance
        instance.phone_number = phone_number
        instance.email = email
        instance.save()

        return instance

# </editor-fold>


# <editor-fold desc="Serializer For User Profile Update ">
class accountsAdminUpdateUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = accountsUserProfileModel
        fields = ["first_name","last_name","date_of_birth","gender","image"]
# </editor-fold>