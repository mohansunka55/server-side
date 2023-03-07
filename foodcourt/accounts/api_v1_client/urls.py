from django.urls import path
from .views import *
urlpatterns = [



    path('all-users/',allUserGenericsView.as_view(),name='allUserGenericsViewURL'),

    # ##LOG IN WITH OTP
    # <editor-fold desc="Phone Number creation">
    path('user-phone-check/',userPhoneCheckRetrieveAPIView.as_view(), name='userPhoneCheckRetrieveAPIViewURL'),

    path('user-enroll-check/', accountsAdminSendOtpForUserCreationAPIView.as_view(), name="accountsAdminSendOtpForUserCreationAPIViewURL"),

    path('user-otp-check/', userOtpCheckAPIView.as_view(), name="userOtpCheckAPIViewURL"),

    path('user-creation/', userCreationRetrieveAPIView.as_view(), name="userCreationRetrieveAPIViewURL"),

    path('user-otp-login/',userOtpValidationRetrieveAPIView.as_view(), name='userOtpValidationRetrieveAPIViewURL'),
    # </editor-fold>

    path('user-email-check/',userEmailCheckRetrieveAPIView.as_view(), name='userEmailCheckRetrieveAPIViewURL'),

    path('user-email-otp-login/',userEmailOtpValidationRetrieveAPIView.as_view(), name='userEmailOtpValidationRetrieveAPIViewURL'),

    path('user-enroll-check-email/', accountsAdminSendOtpForUserCreationToEmailAPIView.as_view(), name="accountsAdminSendOtpForUserCreationToEmailAPIViewURL"),

    path('user-email-otp-check/', userEmailOtpCheckAPIView.as_view(), name="userEmailOtpCheckAPIViewURL"),

    path('user-creation-email/', userCreationEmailRetrieveAPIView.as_view(), name="userCreationEmailRetrieveAPIViewURL"),

    path('user-profile-update/<slug>/', accountsClientUserProfileUpdateDetailsAPIView.as_view(), name="accountsClientUserProfileUpdateDetailsAPIViewURL"),

    path('user-profile-image-update/<slug>/', accountsClientUserProfileUpdateImageDetailsAPIView.as_view(), name="accountsClientUserProfileUpdateImageDetailsAPIViewURL"),

    path('login-user-details/', accountsClientLoginUserDetailsDetailsAPIView.as_view(), name="accountsClientLoginUserDetailsDetailsAPIViewURL"),

    path('user-email-login/', accountsUserLoginGenericsView.as_view(), name="accountsUserLoginGenericsViewURL"),

    path('get-all-referal-codes/', accountsClientGetAllReferalCodesGenericAPIView.as_view(), name="accountsClientGetAllReferalCodesGenericAPIViewURL"),

    ##UPDATE USER PROFILE
    path('profile-update/', accountsClientUserProfileDetailsAPIView.as_view(), name="accountsClientUserProfileDetailsAPIViewURL"),

    path('profile-update-image/', accountsClientUserProfileImageUpdateDetailsAPIView.as_view(),
         name="accountsClientUserProfileImageUpdateDetailsAPIViewURL"),

    ##SEND OTP TO PHONENUMBER
    path('phone-update-otp/', userPhoneUpdateSendOtpAPIView.as_view(), name="userPhoneUpdateSendOtpAPIViewURL"),

    ##UPDATE USER PHONENUMBER
    path('phone-number-update/', accountsClientUserPhoneUpdateGenericsView.as_view(), name="accountsClientUserPhoneUpdateGenericsViewURL"),

    ##SEND OTP TO EMAIL
    path('email-update-otp/', accountClientEmailUpdateOtpRetrieveAPIView.as_view(), name="accountClientEmailUpdateOtpRetrieveAPIViewURL"),

    ##UPDATE USER EMAIL
    path('email-update/', accountsClientUserEmailUpdateGenericsView.as_view(), name="accountsClientUserEmailUpdateGenericsViewURL"),

    path('add-address/', accountsClientAddAddressGenericsView.as_view(),
         name="accountsClientAddAddressGenericsViewURL"),

    path('update-address/', accountsClientUserAddressUpdateAndGetDetailsAPIView.as_view(),
         name="accountsClientUserAddressUpdateAndGetDetailsAPIViewURL"),

    path('user-info/', accountsClientUserInfoDetailsAPIView.as_view(),
         name="accountsClientUserInfoDetailsAPIViewURL"),

    path('user-details/<phone_number>/', accountsClientUserProfileInfoDetailsAPIView.as_view(),
         name="accountsClientUserProfileInfoDetailsAPIViewURL"),

    # <editor-fold desc="USER PROFILE COMPLETE STATS for games">
    path('user-profile-stats-details/', accountsClientUserPlayedCompleteDetailsAPIView.as_view(),
         name="accountsClientUserPlayedCompleteDetailsAPIViewURL"),
    # </editor-fold>

    path('detailed-user-profile/', accountsClientUserProfileSkillScoreDetailsAPIView.as_view(),
         name="accountsClientUserProfileSkillScoreDetailsAPIViewURL"),
]


