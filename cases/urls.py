from django.urls import path
from . import views

urlpatterns = [
    path("", views.case_list, name="case_list"),
    path("new/", views.case_create, name="case_create"),
    path("<int:pk>/edit/", views.case_edit, name="case_edit"),
    path("<int:pk>/delete/", views.case_delete, name="case_delete"),
    path("ajax/cic-exists/", views.cic_exists, name="cic_exists"),
]
