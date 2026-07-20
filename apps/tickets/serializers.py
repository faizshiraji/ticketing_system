from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.serializers import CompanySerializer, UserSerializer

from .models import (
    Category,
    Priority,
    SupportLayer,
    Ticket,
    TicketActivityLog,
    TicketAttachment,
    TicketComment,
    TicketMovement,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "is_active"]


class PrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = ["id", "name", "rank"]


class SupportLayerSerializer(serializers.ModelSerializer):
    agent_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(role__in=[User.Role.AGENT, User.Role.SUPERVISOR, User.Role.ADMIN]),
        source="agents",
        required=False,
    )
    agents = UserSerializer(many=True, read_only=True)

    class Meta:
        model = SupportLayer
        fields = [
            "id",
            "name",
            "level",
            "description",
            "is_active",
            "agents",
            "agent_ids",
        ]


class SupportLayerBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportLayer
        fields = ["id", "name", "level", "is_active"]


class TicketAttachmentSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = TicketAttachment
        fields = ["id", "file", "url", "uploaded_by", "uploaded_at"]
        read_only_fields = ["uploaded_by", "uploaded_at"]

    def get_file(self, obj):
        return self.get_url(obj)

    def get_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return None
        url = obj.file.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class TicketAttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        from .uploads import validate_image_file

        return validate_image_file(value)


class TicketCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = TicketComment
        fields = ["id", "ticket", "author", "body", "is_internal", "created_at", "attachments"]
        read_only_fields = ["author", "created_at"]

    def validate(self, attrs):
        request = self.context["request"]
        if attrs.get("is_internal") and not request.user.is_staff_member:
            raise serializers.ValidationError("Only staff can post internal notes.")
        return attrs


class TicketActivityLogSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = TicketActivityLog
        fields = ["id", "actor", "status_from", "status_to", "note", "created_at"]


class TicketMovementSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    from_agent = UserSerializer(read_only=True)
    to_agent = UserSerializer(read_only=True)
    from_layer = SupportLayerBriefSerializer(read_only=True)
    to_layer = SupportLayerBriefSerializer(read_only=True)

    class Meta:
        model = TicketMovement
        fields = [
            "id",
            "actor",
            "movement_type",
            "from_agent",
            "to_agent",
            "from_layer",
            "to_layer",
            "reason",
            "created_at",
        ]


class TicketListSerializer(serializers.ModelSerializer):
    """Lightweight shape for list views / dashboards."""

    company = CompanySerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    priority = PrioritySerializer(read_only=True)
    support_layer = SupportLayerBriefSerializer(read_only=True)
    is_sla_breached = serializers.BooleanField(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "subject",
            "company",
            "category",
            "priority",
            "support_layer",
            "status",
            "assigned_agent",
            "created_at",
            "resolution_due_at",
            "is_sla_breached",
        ]


class TicketDetailSerializer(TicketListSerializer):
    requester = UserSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    activity_log = TicketActivityLogSerializer(many=True, read_only=True)
    movements = TicketMovementSerializer(many=True, read_only=True)

    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + [
            "description",
            "requester",
            "first_response_due_at",
            "first_responded_at",
            "resolved_at",
            "attachments",
            "comments",
            "activity_log",
            "movements",
        ]

    def get_attachments(self, ticket):
        qs = ticket.attachments.filter(comment__isnull=True).order_by("uploaded_at")
        return TicketAttachmentSerializer(qs, many=True, context=self.context).data

    def get_comments(self, ticket):
        request = self.context["request"]
        qs = ticket.comments.prefetch_related("attachments").all()
        if not request.user.is_staff_member:
            qs = qs.filter(is_internal=False)
        return TicketCommentSerializer(qs, many=True, context=self.context).data


class TicketCreateSerializer(serializers.ModelSerializer):
    """Used for POST — a customer only supplies the fields they should set;
    company/requester are derived server-side in the view, never trusted
    from the request body."""

    class Meta:
        model = Ticket
        fields = ["id", "subject", "description", "category", "priority"]


class EscalateSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["next", "agent"])
    reason = serializers.CharField(min_length=1, trim_whitespace=True)
    target_agent_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs["mode"] == "agent" and not attrs.get("target_agent_id"):
            raise serializers.ValidationError({"target_agent_id": "Required when mode is agent."})
        return attrs
