from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CompanyViewSet, MeView, StaffAgentsListView, UserViewSet

router = DefaultRouter()
router.register("companies", CompanyViewSet, basename="company")
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("agents/", StaffAgentsListView.as_view(), name="staff-agents"),
    path("", include(router.urls)),
]
