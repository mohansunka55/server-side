# from notification.models import notificationMainModel

def user_roles(user):
    role = ""
    if user.is_admin:
        return "Admin"
    if user.is_employee:
        role = "Driver"
    if user.is_supervisor:
        role = "Supervisor"
    if user.is_store_manager:
        role = "Store Manager"
    if user.is_gaurage_manager:
        role = "Garage Manager"
    if user.is_project_manager:
        role = "Project Manager"
    if user.is_project_coordinator:
        role = "Project Coordinator"
    if user.is_head_office:
        role = "Head Office"
    if user.is_main_owner:
        role = "Main Owner"
    return role



#
# def message_to_user(user,message,slug,type,sub_type):
#     already = notificationMainModel.objects.filter(owner=user, message=message,instance_slug=slug)
#     if already:
#         pass
#     else:
#         create_notify = notificationMainModel.objects.create(owner=user, message=message,
#                                                              instance_slug=slug, type=type, sub_type=sub_type)
#
#
#
# from geopy.geocoders import Nominatim
#
#
# def location_check(Latitude,Longitude):
#     """
#     andhra pradesh : lat "15.9129":,long "79.7400"
#     sikkim: lat "27.5330":,long "88.5122"
#     nagaland: lat "26.1584":,long "94.5624"
#     odisha: lat "20.9517":,long "85.0985"
#     telangana: lat "18.1124":,long "79.0193"
#     assam: lat "26.2006":,long "92.9376"
#
#     """
#     Latitude = Latitude
#     Longitude = Longitude
#     geolocator = Nominatim(user_agent="geoapiExercises")
#     location = geolocator.reverse(Latitude + "," + Longitude)
#     address = location.raw["address"]
#     state = address.get("state","")
#     not_allowed_states = ["andhra pradesh","assam","nagaland","odisha","sikkim","telangana"]
#     if state == None:
#         return False
#     for each_state in not_allowed_states:
#         if state.lower() in each_state:
#             return False
#     else:
#         return True
