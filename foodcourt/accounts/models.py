import string

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.signals import pre_save
from django.utils.crypto import get_random_string

from foodcourt.utils import slug_pre_save_receiver


# <editor-fold desc="Custom User Manager">
class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None):
        if phone_number == None:
            raise ValueError("phone number")
        else:
            user = self.model(
                phone_number=phone_number,
                # password=password
            )
        user.is_approved = True
        user.is_active = True
        user.employee_id = get_random_string(7, string.ascii_uppercase + string.digits)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_customer(self, phone_number, email=None, password=None):
        user = self.create_user(
            phone_number=phone_number,
            password=password,
        )
        user.is_customer = True
        if email:
            user.email = self.normalize_email(email)
        user.save(using=self._db)
        return user

    def create_supervisor(self, phone_number, email=None, password=None):
        user = self.create_user(
            phone_number=phone_number,
            password=password,
        )
        user.is_supervisor = True
        if email:
            user.email = self.normalize_email(email)
        user.save(using=self._db)
        return user

    def create_store_manager(self, phone_number, email=None, password=None):
        user = self.create_user(
            password=password,
            phone_number=phone_number,
        )
        user.is_store_manager = True
        if email:
            user.email = self.normalize_email(email)
        user.save(using=self._db)
        return user


    def create_staff(self, phone_number, email=None, password=None):
        user = self.create_user(
            password=password,
            phone_number=phone_number,
        )
        if email:
            user.email = self.normalize_email(email)
        user.is_staff = True
        user.save(using=self._db)
        return user



    def create_superuser(self, phone_number, password=None):
        user = self.create_user(
            password=password,
            phone_number=phone_number,
        )
        user.is_superuser=True
        user.is_staff = True
        user.is_admin = True
        user.is_customer = True
        user.is_store_manager = True
        user.is_sales_and_marketing = True
        user.is_service = True
        user.is_analytics=True
        # user.employee_id = get_random_string(7, string.ascii_uppercase+string.digits)
        user.save(using=self._db)
        return user


# </editor-fold>


# <editor-fold desc="Abstract Base User Model">

"""
E-commerce management involves several user roles that are essential to the functioning of an e-commerce platform. These roles may vary depending on the size and complexity of the platform, but some common user roles include:

Administrator: The administrator is responsible for managing the overall e-commerce platform, including the configuration and maintenance of the system. They ensure that the platform is functioning smoothly, and troubleshoot any issues that arise.

Store Manager: The store manager is responsible for managing the day-to-day operations of the e-commerce store. They oversee product listings, manage inventory, process orders, and handle customer service inquiries.

Sales and Marketing: This user role is responsible for developing and executing sales and marketing strategies to promote the e-commerce platform and drive sales. This includes managing social media accounts, email marketing campaigns, and advertising efforts.

Customer Service: The customer service user role is responsible for managing customer inquiries and resolving any issues that arise. They may interact with customers via email, phone, or chat to provide support and assistance.

Analytics: The analytics user role is responsible for monitoring and analyzing data related to e-commerce performance, including website traffic, customer behavior, and sales data. They use this information to make data-driven decisions and improve the performance of the e-commerce platform.
"""
class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.BigIntegerField(verbose_name='Phone Number', unique=True)
    employee_id = models.CharField(unique=True, max_length=255)
    email = models.EmailField(verbose_name='Email Address', blank=True, max_length=255, null=True, unique=True)
    name = models.CharField(verbose_name='Name',max_length=100,null=True, blank=True,unique=False)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    is_store_manager=models.BooleanField(default=False)
    is_sales_and_marketing=models.BooleanField(default=False)
    is_service=models.BooleanField(default=False)
    is_analytics=models.BooleanField(default=False)

    slug = models.SlugField(max_length=250, null=True, blank=True, unique=True)
    date_created = models.DateField(auto_now_add=True)

    USERNAME_FIELD = 'phone_number'

    objects = CustomUserManager()

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return str(self.phone_number)

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    # @property
    # def get_lives(self):
    #     return self.accountsUserAddressModel_owner.address

    @property
    def name(self):
        return f"{self.accountsUserProfileModel_owner.first_name} {self.accountsUserProfileModel_owner.last_name}"

    def techanician(self):
        return self.vehicleAssignUserModel_owner.all().count()
    def get_employees_image(self):
        try:
            return self.accountsUserProfileModel_owner.image.url
        except:
            return ""

    def get_employees_name(self):
        try:
            return self.accountsUserProfileModel_owner.name
        except:
            return ""


pre_save.connect(slug_pre_save_receiver, sender=User)


# </editor-fold>

#
# # <editor-fold desc="Account departments">
# class accountsDepartmentModel(models.Model):
#     title = models.CharField(max_length=200)
#     description = models.TextField()
#     date_created = models.DateTimeField(auto_now_add=True)
#     slug = models.SlugField(max_length=250, null=True, blank=True, unique=True)
#
#     class Meta:
#         ordering = ['-id']
#
#     def __str__(self):
#         return self.title
#
#
# pre_save.connect(slug_pre_save_receiver, sender=accountsDepartmentModel)
# # </editor-fold>


#
# # <editor-fold desc="User Profile Model">
# class accountsUserProfileModel(models.Model):
#     owner = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, primary_key=True,
#                                  related_name='accountsUserProfileModel_owner')
#     first_name = models.CharField(max_length=100)
#     last_name = models.CharField(max_length=100)
#     date_of_birth = models.DateField(null=True, blank=True)
#     gender = models.CharField(max_length=100, choices=GenderEnumTypes.choices(), blank=True, null=True)
#     id_Proof = models.CharField(max_length=100)
#     image = models.ImageField(upload_to='accounts/profile/images/', blank=True, null=True)
#     department= models.ForeignKey(accountsDepartmentModel, on_delete=models.CASCADE,
#                                    related_name="accountsUserProfileModel_department",null=True,blank=True)
#     #
#     # date_of_birth = models.DateField(null=True, blank=True)
#     date_created = models.DateTimeField(auto_now_add=True)
#     slug = models.SlugField(max_length=250, null=True, blank=True, unique=True)
#
#     class Meta:
#         ordering = ['-date_created']
#
#     def get_employees_image(self):
#         return self.image.url
#
#     @property
#     def name(self):
#         return f"{self.first_name} {self.last_name}"
#
#     @property
#     def age(self):
#         try:
#             age = int((datetime.date.today() - self.date_of_birth).days / 365.25)
#         except:
#             age = ''
#         return age
#
#
# pre_save.connect(slug_pre_save_receiver, sender=accountsUserProfileModel)
#
#
# # </editor-fold>


# # <editor-fold desc="User LogIn OTP Model">
# class accountsUserLoginOtpModel(models.Model):
#     owner = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING,
#                               related_name="accountsUserLoginOtpModel_user")
#     otp = models.BigIntegerField()
#     active = models.BooleanField(default=True)
#     date_created = models.DateField(auto_now_add=True)
#     slug = models.SlugField(max_length=250, null=True, blank=True, unique=True)
#     class Meta:
#         ordering = ['-id']
#
# pre_save.connect(slug_pre_save_receiver, sender=accountsUserLoginOtpModel)
#
#
# # post_save.connect(expire_OTP_when_new_otp_generated, sender=accountsUserLoginOtpModel)
# # </editor-fold>
#
#
# # <editor-fold desc="User Creation OTP Model">
# class accountsAdminUserCreationLoginOtpModel(models.Model):
#     otp = models.IntegerField()
#     phone_number = models.BigIntegerField(null=True, blank=True)
#     active = models.BooleanField(default=True)
#     date_created = models.DateTimeField(auto_now_add=True)
#     slug = models.SlugField(max_length=250, null=True, blank=True, unique=True)
#
#     class Meta:
#         ordering = ['-id']
# pre_save.connect(slug_pre_save_receiver, sender=accountsAdminUserCreationLoginOtpModel)
#
#
# # </editor-fold>
#
#
# # <editor-fold desc="User Address Model">
# class accountsUserAddressModel(models.Model):
#     owner = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, primary_key=True,
#                                  related_name='accountsUserAddressModel_owner')
#     address = models.CharField(max_length=250)
#     pincode = models.IntegerField(null=True,blank=True)
#     city = models.ForeignKey(coreUtilsCityModel, on_delete=models.DO_NOTHING, related_name="accountsUserAddressModel")
#     state = models.ForeignKey(coreUtilsStatesModel, on_delete=models.DO_NOTHING,
#                               related_name="accountsUserAddressModel")
#     country = models.ForeignKey(coreUtilsCountryModel, on_delete=models.DO_NOTHING,
#                                 related_name="accountsUserAddressModel")
#     address_proof = models.FileField(upload_to='accounts/useraddress/files/', blank=True, null=True)
#
#     date_created = models.DateTimeField(auto_now_add=True)
#     slug = models.SlugField(max_length=250, null=True, blank=True, unique=True)
#     class Meta:
#         ordering = ['-date_created']
#     @property
#     def user_city(self):
#         try:
#             return self.city.city
#         except:
#             return ""
#     @property
#     def user_state(self):
#         try:
#             return self.state.states
#         except:
#             return ""
#
#     @property
#     def user_country(self):
#         try:
#             return self.country.country
#         except:
#             return ""
#
#
#
# pre_save.connect(slug_pre_save_receiver, sender=accountsUserAddressModel)
# # </editor-fold>
