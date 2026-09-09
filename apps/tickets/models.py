from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.accounts.models import Company


class Category(models.Model):
    """E.g. Billing, Network outage, Provisioning, General inquiry."""

    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Priority(models.Model):
    """E.g. Low, Medium, High, Critical — ordered by `rank` for sorting."""

    name = models.CharField(max_length=50, unique=True)
    rank = models.PositiveSmallIntegerField(
        help_text="Lower rank = higher urgency. Used for default sort order."
    )

    class Meta:
        verbose_name_plural = "priorities"
        ordering = ["rank"]

    def __str__(self):
        return self.name


class SupportLayer(models.Model):
    """
    Support tier (e.g. L1 Frontline, L2 Advanced). Lower `level` is first-line.
    Agents are assigned via M2M; tickets track their current layer for escalation.
    """

    name = models.CharField(max_length=100, unique=True)
    level = models.PositiveSmallIntegerField(
        unique=True, help_text="Lower = first line. Escalation moves to a higher level."
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    agents = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="support_layers",
        limit_choices_to={"role__in": ["agent", "supervisor", "admin"]},
    )

    class Meta:
        ordering = ["level"]

    def __str__(self):
        return f"L{self.level} {self.name}"


class SLAPolicy(models.Model):
    """
    Response/resolution targets per priority + category combination.
    Category is optional — leave blank for a priority-wide default.
    """

    priority = models.ForeignKey(Priority, on_delete=models.CASCADE, related_name="sla_policies")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="sla_policies", null=True, blank=True
    )
    first_response_minutes = models.PositiveIntegerField()
    resolution_minutes = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["priority", "category"], name="unique_sla_per_priority_category"
            )
        ]

    def __str__(self):
        scope = self.category.name if self.category else "all categories"
        return f"{self.priority.name} / {scope}"


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RECEIVED = "received", "Received"
        IN_PROGRESS = "in_progress", "In progress"
        ON_HOLD = "on_hold", "On hold"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"
        REOPENED = "reopened", "Reopened"

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="tickets")
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets_raised"
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tickets_assigned",
        null=True,
        blank=True,
    )
    support_layer = models.ForeignKey(
        "SupportLayer",
        on_delete=models.PROTECT,
        related_name="tickets",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="tickets")
    priority = models.ForeignKey(Priority, on_delete=models.PROTECT, related_name="tickets")

    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    first_response_due_at = models.DateTimeField(null=True, blank=True)
    resolution_due_at = models.DateTimeField(null=True, blank=True)
    first_responded_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["assigned_agent", "status"]),
        ]

    def __str__(self):
        return f"#{self.pk} {self.subject}"

    def apply_sla(self):
        """Set due-at timestamps from the matching SLAPolicy. Called on create."""
        policy = (
            SLAPolicy.objects.filter(priority=self.priority, category=self.category).first()
            or SLAPolicy.objects.filter(priority=self.priority, category__isnull=True).first()
        )
        first_response_minutes = (
            policy.first_response_minutes
            if policy
            else settings.DEFAULT_FIRST_RESPONSE_MINUTES
        )
        resolution_minutes = (
            policy.resolution_minutes if policy else settings.DEFAULT_RESOLUTION_MINUTES
        )
        now = timezone.now()
        self.first_response_due_at = now + timezone.timedelta(minutes=first_response_minutes)
        self.resolution_due_at = now + timezone.timedelta(minutes=resolution_minutes)

    @property
    def is_sla_breached(self):
        now = timezone.now()
        if self.status in {self.Status.RESOLVED, self.Status.CLOSED}:
            return False
        if self.first_responded_at is None and self.first_response_due_at and now > self.first_response_due_at:
            return True
        if self.resolution_due_at and now > self.resolution_due_at:
            return True
        return False


class TicketComment(models.Model):
    """A reply on a ticket thread. `is_internal` hides it from the customer."""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField()
    is_internal = models.BooleanField(
        default=False, help_text="Internal notes are visible to staff only."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment on #{self.ticket_id} by {self.author}"


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    comment = models.ForeignKey(
        TicketComment, on_delete=models.CASCADE, related_name="attachments", null=True, blank=True
    )
    file = models.FileField(upload_to="ticket_attachments/%Y/%m/")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name


class TicketActivityLog(models.Model):
    """
    Immutable audit trail of every status change. This table is the
    primary data source for dashboard analytics (resolution time,
    reopen rate, first-response time).
    """

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="activity_log")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status_from = models.CharField(max_length=20, blank=True)
    status_to = models.CharField(max_length=20)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"#{self.ticket_id}: {self.status_from} -> {self.status_to}"


class TicketMovement(models.Model):
    """Immutable history of assignment / escalation moves between agents and layers."""

    class MovementType(models.TextChoices):
        ASSIGN = "assign", "Assign"
        ESCALATE_NEXT = "escalate_next", "Escalate to next layer"
        ESCALATE_AGENT = "escalate_agent", "Escalate to agent"
        REASSIGN = "reassign", "Reassign"

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="movements")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ticket_movements_made",
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    from_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    to_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    from_layer = models.ForeignKey(
        SupportLayer, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    to_layer = models.ForeignKey(
        SupportLayer, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"#{self.ticket_id} {self.movement_type}"
