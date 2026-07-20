from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.notifications.services import (
    notify_ticket_assigned,
    notify_ticket_created,
    notify_ticket_status_changed,
)

from .models import Ticket, TicketActivityLog, TicketComment


@receiver(pre_save, sender=Ticket)
def _stash_previous_status(sender, instance, **kwargs):
    """Remember the DB status before save so post_save can detect a change."""
    if instance.pk:
        previous = Ticket.objects.filter(pk=instance.pk).values("status", "assigned_agent_id").first()
        instance._previous_status = previous["status"] if previous else None
        instance._previous_agent_id = previous["assigned_agent_id"] if previous else None
    else:
        instance._previous_status = None
        instance._previous_agent_id = None


@receiver(post_save, sender=Ticket)
def _log_and_notify(sender, instance, created, **kwargs):
    if created:
        instance.apply_sla()
        # apply_sla only sets in-memory fields; persist without re-triggering signals recursively
        Ticket.objects.filter(pk=instance.pk).update(
            first_response_due_at=instance.first_response_due_at,
            resolution_due_at=instance.resolution_due_at,
        )
        TicketActivityLog.objects.create(
            ticket=instance, actor=instance.requester, status_from="", status_to=instance.status
        )
        notify_ticket_created(instance)
        return

    previous_status = getattr(instance, "_previous_status", None)
    if previous_status is not None and previous_status != instance.status:
        TicketActivityLog.objects.create(
            ticket=instance,
            actor=instance.assigned_agent,
            status_from=previous_status,
            status_to=instance.status,
        )
        if instance.status == Ticket.Status.RESOLVED and not instance.resolved_at:
            Ticket.objects.filter(pk=instance.pk).update(resolved_at=timezone.now())
        notify_ticket_status_changed(instance, previous_status)

    previous_agent_id = getattr(instance, "_previous_agent_id", None)
    if instance.assigned_agent_id and previous_agent_id != instance.assigned_agent_id:
        notify_ticket_assigned(instance)


@receiver(post_save, sender=TicketComment)
def _mark_first_response(sender, instance, created, **kwargs):
    """The first non-internal staff reply satisfies the first-response SLA."""
    if not created or instance.is_internal:
        return
    ticket = instance.ticket
    if instance.author.is_staff_member and ticket.first_responded_at is None:
        Ticket.objects.filter(pk=ticket.pk).update(first_responded_at=timezone.now())
