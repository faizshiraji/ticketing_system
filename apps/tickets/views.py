from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import IsStaffMember, IsSupervisorOrAdmin
from apps.accounts.serializers import UserSerializer

from .models import Category, Priority, SupportLayer, Ticket, TicketAttachment, TicketComment, TicketMovement
from .serializers import (
    CategorySerializer,
    EscalateSerializer,
    PrioritySerializer,
    SupportLayerSerializer,
    TicketAttachmentSerializer,
    TicketAttachmentUploadSerializer,
    TicketCommentSerializer,
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
)
from .services import escalate_ticket, lowest_active_layer, record_movement
from .uploads import collect_upload_files


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        user = self.request.user
        qs = Category.objects.all()
        if getattr(user, "role", None) in {"supervisor", "admin"}:
            return qs
        return qs.filter(is_active=True)

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsSupervisorOrAdmin()]
        return [permissions.IsAuthenticated()]


class PriorityViewSet(viewsets.ModelViewSet):
    queryset = Priority.objects.all()
    serializer_class = PrioritySerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsSupervisorOrAdmin()]
        return [permissions.IsAuthenticated()]


class SupportLayerViewSet(viewsets.ModelViewSet):
    serializer_class = SupportLayerSerializer
    queryset = SupportLayer.objects.prefetch_related("agents").all()

    def get_queryset(self):
        qs = SupportLayer.objects.prefetch_related("agents").all()
        user = self.request.user
        if getattr(user, "role", None) in {"supervisor", "admin"}:
            return qs
        return qs.filter(is_active=True)

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsSupervisorOrAdmin()]
        return [IsStaffMember()]

    @action(detail=True, methods=["get"], url_path="agents")
    def agents(self, request, pk=None):
        layer = self.get_object()
        agents = layer.agents.filter(
            role__in=[User.Role.AGENT, User.Role.SUPERVISOR, User.Role.ADMIN],
            is_active=True,
        ).order_by("username")
        return Response(UserSerializer(agents, many=True).data)


class TicketViewSet(viewsets.ModelViewSet):
    """
    Customers: see only tickets they raised, within their own company.
    Agents/supervisors/admins: see tickets across companies; agents are
    expected to filter by ?assigned_agent=me at the client level, or by
    company/status via query params (django-filter wired via settings).
    """

    filterset_fields = ["status", "company", "priority", "category", "assigned_agent", "support_layer"]

    def get_queryset(self):
        user = self.request.user
        qs = Ticket.objects.select_related(
            "company", "category", "priority", "assigned_agent", "support_layer"
        ).prefetch_related("movements__actor", "movements__from_agent", "movements__to_agent")
        if user.is_customer:
            return qs.filter(requester=user, company=user.company)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return TicketCreateSerializer
        if self.action == "list":
            return TicketListSerializer
        return TicketDetailSerializer

    def perform_create(self, serializer):
        user = self.request.user
        layer = lowest_active_layer()
        if user.is_customer:
            serializer.save(requester=user, company=user.company, support_layer=layer)
        else:
            serializer.save(requester=user, company=user.company, support_layer=layer)

    def perform_update(self, serializer):
        user = self.request.user
        if user.is_customer:
            raise PermissionDenied("Customers cannot modify ticket status or assignment.")

        ticket = self.get_object()
        previous_agent = ticket.assigned_agent
        previous_layer = ticket.support_layer

        serializer.save()
        ticket.refresh_from_db()

        new_agent_id = ticket.assigned_agent_id
        if new_agent_id != (previous_agent.id if previous_agent else None):
            movement_type = (
                TicketMovement.MovementType.ASSIGN
                if previous_agent is None
                else TicketMovement.MovementType.REASSIGN
            )
            reason = "Assigned to self" if new_agent_id == user.id else "Assignment updated"
            record_movement(
                ticket=ticket,
                actor=user,
                movement_type=movement_type,
                reason=reason,
                from_agent=previous_agent,
                to_agent=ticket.assigned_agent,
                from_layer=previous_layer,
                to_layer=ticket.support_layer,
            )

    @action(detail=True, methods=["post"], permission_classes=[IsStaffMember])
    def escalate(self, request, pk=None):
        ticket = self.get_object()
        ser = EscalateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            escalate_ticket(
                ticket=ticket,
                actor=request.user,
                mode=ser.validated_data["mode"],
                reason=ser.validated_data["reason"],
                target_agent_id=ser.validated_data.get("target_agent_id"),
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        ticket.refresh_from_db()
        return Response(
            TicketDetailSerializer(ticket, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="attachments")
    def attachments(self, request, pk=None):
        ticket = self.get_object()
        user = request.user
        if user.is_customer and ticket.requester_id != user.id:
            raise PermissionDenied("You can only attach files to your own tickets.")

        ser = TicketAttachmentUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        attachment = TicketAttachment.objects.create(
            ticket=ticket,
            file=ser.validated_data["file"],
            uploaded_by=user,
            comment=None,
        )
        return Response(
            TicketAttachmentSerializer(attachment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class TicketCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TicketCommentSerializer

    def get_queryset(self):
        user = self.request.user
        qs = TicketComment.objects.filter(ticket_id=self.kwargs["ticket_pk"]).prefetch_related(
            "attachments"
        )
        if not user.is_staff_member:
            qs = qs.filter(is_internal=False)
        return qs

    def create(self, request, *args, **kwargs):
        ticket = Ticket.objects.get(pk=self.kwargs["ticket_pk"])
        user = request.user
        if user.is_customer and ticket.requester_id != user.id:
            raise PermissionDenied("You can only comment on your own tickets.")

        files = collect_upload_files(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(ticket=ticket, author=user)
        for uploaded in files:
            TicketAttachment.objects.create(
                ticket=ticket,
                comment=comment,
                file=uploaded,
                uploaded_by=user,
            )
        comment.refresh_from_db()
        out = TicketCommentSerializer(comment, context={"request": request})
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        ticket = Ticket.objects.get(pk=self.kwargs["ticket_pk"])
        user = self.request.user
        if user.is_customer and ticket.requester_id != user.id:
            raise PermissionDenied("You can only comment on your own tickets.")
        serializer.save(ticket=ticket, author=user)
