from rest_framework.permissions import BasePermission

from .models import User


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == User.Role.CUSTOMER)


class IsStaffMember(BasePermission):
    """Agents, supervisors, and admins — i.e. anyone internal."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff_member)


class IsSupervisorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.role in {User.Role.SUPERVISOR, User.Role.ADMIN}
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == User.Role.ADMIN)
