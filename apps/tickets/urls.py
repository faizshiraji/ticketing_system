from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    PriorityViewSet,
    SupportLayerViewSet,
    TicketCommentViewSet,
    TicketViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("priorities", PriorityViewSet, basename="priority")
router.register("support-layers", SupportLayerViewSet, basename="support-layer")
router.register("", TicketViewSet, basename="ticket")

comment_list = TicketCommentViewSet.as_view({"get": "list", "post": "create"})
comment_detail = TicketCommentViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("<int:ticket_pk>/comments/", comment_list, name="ticket-comments-list"),
    path("<int:ticket_pk>/comments/<int:pk>/", comment_detail, name="ticket-comments-detail"),
    path("", include(router.urls)),
]
