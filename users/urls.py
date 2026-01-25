from django.urls import path
from . import views, views_groups
from .views_groups import group_create_ajax, group_invite
from .views_auth import signup

urlpatterns = [
    path("groups/", views_groups.group_list, name="group_list"),
    path("profile/", views.profile, name="profile"),
    path("groups/new/", views_groups.group_create, name="group_create"),
    path("groups/<int:pk>/", views_groups.group_detail, name="group_detail"),
    path("groups/<int:pk>/members/", views_groups.group_members, name="group_members"),
    path("groups/<int:group_id>/leave/", views.group_leave, name="group_leave"),
    path("groups/create-ajax/", group_create_ajax, name="group_create_ajax"),
    path("signup/", signup, name="signup"),
    path("groups/<int:group_id>/invite/", group_invite, name="group_invite"),
]
