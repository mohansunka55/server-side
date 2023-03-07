from django.urls import path
from .views import (accountsAdminBasicUserStatsGenericsView, userOtpValidationRetrieveAPIView,
                    userPhoneCheckRetrieveAPIView, accountsAdminAllUserGenericsView,
                    accountsAdminAllUserGenericsDetailView, accountsAdminUserLoginGenericsView,
                    accountsAdminAllUsersGenericsView,
                    accountsAdminUserAboutDetailsAPIView, accountsAdminSupervisorRegistrationGenericsView,
                    accountAdminProjectManagerGenericApiView,
                    accountsAdminUserPermissionDetailsAPIView, accountAdminProjectCoordinatorGenericApiView,
                    accountAdminHeadOfficeGenericApiView, accountAdminMainOwnerGenericApiView,
                    accountsAdminUserProfileAttendanceGenericsView, accountsAdminUsersPermissionsGenericsView,
                    accountsAdminUsersPermissionsGenericsViewDetailsAPIView,
                    accountsAdminUserSpecificProjectsGenericsView,
                    accountsAdminUserSpecificProjectsDetailsAPIView, accountAdminEmployeeGenericApiView,
                    accountAdminSupervisorGenericApiView, accountAdminStoremanagerGenericApiView,
                    accountAdminGarageManagerGenericApiView, allUserGenericsView,
                    accountsAdminLoginUserAttendanceStatsDetailsAPIView,
                    accountsAdminUserProfileAttendanceDetailsAPIView, accountsAdminUserDetailsAPIView,
                    accountsAdminUserProfileUpdateDetailsAPIView)

urlpatterns = [



    # <editor-fold desc="POST: Apis For Supervisor and Its Data Creation">
    path('supervisor-register/', accountsAdminSupervisorRegistrationGenericsView.as_view(), name="accountsAdminSupervisorRegistrationGenericsViewURL"),
    # </editor-fold>


    # <editor-fold desc="POST: Apis For User LogIn with employee_id and Password">
    path('user-login/', accountsAdminUserLoginGenericsView.as_view(), name="accountsAdminUserLoginGenericsViewURL"),
    # </editor-fold>

    # <editor-fold desc="GET: Apis For Get all User">
    path('get-all-users/', accountsAdminAllUsersGenericsView.as_view(), name="accountsAdminAllUsersGenericsViewURL"),
    # </editor-fold>

    # <editor-fold desc="GET And PUT: Apis For get User Details">
    path('user-details/<slug>/', accountsAdminUserAboutDetailsAPIView.as_view(), name="accountsAdminUserAboutDetailsAPIViewURL"),
    # </editor-fold>


    # <editor-fold desc="USER BASIC STATUS">
    path('user-stats/', accountsAdminBasicUserStatsGenericsView.as_view(),
         name='accountsAdminBasicUserStatsGenericsViewURL'),
    # </editor-fold>


    # <editor-fold desc="Get All User With Profile">
    path("all-users/", accountsAdminAllUserGenericsView.as_view(), name="accountsAdminAllUserGenericsViewURL"),
    # </editor-fold>

    # <editor-fold desc="Get An User and Profile With slug">
    path("all-users/<slug>/", accountsAdminAllUserGenericsDetailView.as_view(), name="accountsAdminAllUserGenericsDetailViewURL"),
    # </editor-fold>

    # <editor-fold desc="Post User address with slug">
    # path("create-user-address/<slug>/", accountsAdminPostUserAddressDetailView.as_view(),
    #      name="accountsAdminAllUserAddressDetailViewURL"),
    # </editor-fold>

    # <editor-fold desc="Get User address with slug">
    # path("user-address/<slug>/", accountsAdminAllUserAddressDetailView.as_view(), name="accountsAdminAllUserAddressDetailViewURL"),
    # </editor-fold>
    # path('user-phone-check/', userPhoneCheckRetrieveAPIView.as_view(), name='userPhoneCheckRetrieveAPIViewURL'),
    #
    # # path('user-otp-login/', userOtpValidationRetrieveAPIView.as_view(), name='userOtpValidationRetrieveAPIViewURL'),
    #
    # # path('employee-id-login/', accountsUserEmployeeIdPasswordLoginGenericsView.as_view(), name = "accountsUserEmployeeIdPasswordLoginGenericsViewURL"),
    #
    # # path('customer-creation/', userCreationRetrieveAPIView.as_view(), name="userCreationRetrieveAPIViewURL"),
    #
    # # path('user-phone-check/', userPhoneCheckRetrieveAPIView.as_view(), name='userPhoneCheckRetrieveAPIViewURL'),
    # # path('user-otp-login/', userOtpValidationRetrieveAPIView.as_view(), name='userOtpValidationRetrieveAPIViewURL'),
    #
    # path('user-otp-login/', userOtpValidationRetrieveAPIView.as_view(), name='userOtpValidationRetrieveAPIViewURL'),


    ##LOG IN WITH OTP
    path('user-phone-check/',userPhoneCheckRetrieveAPIView.as_view(), name='userPhoneCheckRetrieveAPIViewURL'),
    path('user-otp-login/',userOtpValidationRetrieveAPIView.as_view(), name='userOtpValidationRetrieveAPIViewURL'),



    #new users create

    # <editor-fold desc="Api For Employee Create">
    path('employee-create/', accountAdminEmployeeGenericApiView.as_view(),name="accountAdminEmployeeGenericApiViewURL"),
    # </editor-fold>
    # <editor-fold desc="Api For Supervisor Create">
    path('supervisor-create/', accountAdminSupervisorGenericApiView.as_view(),name="accountAdminSupervisorGenericApiViewURL"),
    # </editor-fold>

    # <editor-fold desc="Api For Store manager create">
    path('store-manager-create/', accountAdminStoremanagerGenericApiView.as_view(),name="accountAdminStoremanagerGenericApiViewURL"),
    # </editor-fold>

    # <editor-fold desc="Api For Garage Manager create">
    path('garage-manager-create/', accountAdminGarageManagerGenericApiView.as_view(),name="accountAdminGarageManagerGenericApiViewURL"),
    # </editor-fold>

    # <editor-fold desc="Api For project manager Create">
    path('project-manager-create/', accountAdminProjectManagerGenericApiView.as_view(),name="accountAdminProjectManagerGenericApiViewURL"),
    # </editor-fold>

    # <editor-fold desc="Post Api For Project Coordinator Create">
    path('project-coordinator-create/', accountAdminProjectCoordinatorGenericApiView.as_view(),
         name="accountAdminProjectCoordinatorGenericApiViewURL"),
    # </editor-fold>

    # <editor-fold desc="Post Api For head Officer Create">
    path('head-officer-create/', accountAdminHeadOfficeGenericApiView.as_view(),name="accountAdminHeadOfficeGenericApiViewURL"),
    # </editor-fold>

    # <editor-fold desc="Post Api For main owner Create">
    path('main-owner-create/', accountAdminMainOwnerGenericApiView.as_view(),name="accountAdminMainOwnerGenericApiViewURL"),
    # </editor-fold>

    # <editor-fold desc="Api For get all user permissions GET and PUT">
    path('user-permissions/<slug>/', accountsAdminUserPermissionDetailsAPIView.as_view(),
         name="accountsAdminUserPermissionDetailsAPIViewURL"),
    # </editor-fold>


    # # <editor-fold desc="view user detail ">
    # path('view-user-detail/<slug>/',accountsAdminViewUserAboutDetailsAPIView.as_view(),name="accountsAdminViewUserAboutDetailsAPIViewURL"),
    # # </editor-fold>



    # <editor-fold desc="USER PROFILE DETAILS WITH ATTENDANCE DETAILS">
    path('users-profile-attendance/',accountsAdminUserProfileAttendanceGenericsView.as_view(),name = "accountsAdminUserProfileAttendanceGenericsViewURL"),
    # </editor-fold>

    ##LOGIN USER DETAILS
    path('users-profile-attendance/<slug>/',accountsAdminUserProfileAttendanceDetailsAPIView.as_view(),name = "accountsAdminUserProfileAttendanceDetailsAPIViewURL"),

    ##USERS ALL PERMISSION DETAILS
    path('users-permissions/',accountsAdminUsersPermissionsGenericsView.as_view(),name = "accountsAdminUsersPermissionsGenericsViewURL"),
    path('users-permissions/<slug>/',accountsAdminUsersPermissionsGenericsViewDetailsAPIView.as_view(),name = "accountsAdminUsersPermissionsGenericsViewDetailsAPIViewURL"),


    ##USERS SPECIFIC PROJECTS
    path('user-specific-projects/',accountsAdminUserSpecificProjectsGenericsView.as_view(), name = "accountsAdminUserSpecificProjectsGenericsViewURL"),
    path('user-specific-projects/<slug>/',accountsAdminUserSpecificProjectsDetailsAPIView.as_view(), name = "accountsAdminUserSpecificProjectsDetailsAPIViewURL"),

    # new adding from client side
    # path('all-users/', allUserGenericsView.as_view(), name='allUserGenericsViewURL'),

    ##USER ATTENDANCE STATS
    # path('login-user-attendance/',accountsAdminLoginUserAttendanceStatsGenericsView.as_view(),name="accountsAdminLoginUserAttendanceStatsGenericsViewURL"),

    path('login-user-attendance/<slug>/',accountsAdminLoginUserAttendanceStatsDetailsAPIView.as_view(),name="accountsAdminLoginUserAttendanceStatsDetailsAPIViewURL"),


    # <editor-fold desc="update user email and phone">
    path('employee-update/<slug>/', accountsAdminUserDetailsAPIView.as_view(),
         name="accountsAdminUserDetailsAPIViewURL"),
    # </editor-fold>

    # user profile update
    path('user-profile-update/<slug>/', accountsAdminUserProfileUpdateDetailsAPIView.as_view(),
         name="accountsAdminUserProfileUpdateDetailsAPIViewURL"),

]
