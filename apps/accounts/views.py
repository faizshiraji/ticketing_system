from rest_framework import viewsets
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Company, User
from .permissions import IsAdmin, IsStaffMember, IsSupervisorOrAdmin
from .serializers import CompanySerializer, MeSerializer, StaffAgentSerializer, UserAdminSerializer, UserSerializer


class MeView(RetrieveAPIView):
    """Returns the logged-in user's own profile (customer or staff)."""

    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class PublicCompanyListView(ListAPIView):
    """Unauthenticated list of active companies for the login dropdown."""

    permission_classes = [AllowAny]
    serializer_class = CompanySerializer
    pagination_class = None

    def get_queryset(self):
        return Company.objects.filter(is_active=True).order_by("name")


class CompanyViewSet(viewsets.ModelViewSet):
    """
    Staff can list/retrieve companies.
    Supervisors and admins can create/update/destroy.
    """

    queryset = Company.objects.all().order_by("name")
    serializer_class = CompanySerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsSupervisorOrAdmin()]
        return [IsStaffMember()]


class UserViewSet(viewsets.ModelViewSet):
    """
    Supervisors and admins can list/retrieve users.
    Only admins can create/update/destroy.
    """

    queryset = User.objects.select_related("company").order_by("username")
    serializer_class = UserAdminSerializer
    filterset_fields = ["role", "company", "is_active"]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdmin()]
        return [IsSupervisorOrAdmin()]


class StaffAgentsListView(ListAPIView):
    """Staff-readable list of agents/supervisors/admins for escalation pickers."""

    permission_classes = [IsStaffMember]
    serializer_class = StaffAgentSerializer

    def get_queryset(self):
        return (
            User.objects.filter(
                role__in=[User.Role.AGENT, User.Role.SUPERVISOR, User.Role.ADMIN],
                is_active=True,
            )
            .prefetch_related("support_layers")
            .order_by("username")
        )
