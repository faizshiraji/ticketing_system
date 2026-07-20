"""
Synchronous notifications - no Celery/Redis in this phase.

Every function here is defensive: a notification failure (bad SMTP config,
network blip) must never break the ticket save that triggered it. Errors
are logged, not raised.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send_email(subject, message, to_email):
    if not to_email:
        return
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)
    except Exception:
        logger.exception("Failed to send notification email to %s", to_email)


def _send_sms(phone, message):
    """
    Placeholder for an SMS gateway integration (e.g. a local BD SMS
    aggregator). Wire in the actual provider call here when one is
    chosen - keeping this as a single seam means the rest of the codebase
    never needs to know which provider is in use.
    """
    if not phone:
        return
    logger.info("SMS (not yet wired to a provider) to %s: %s", phone, message)


def notify_ticket_created(ticket):
    _send_email(
        subject=f"[Ticket #{ticket.id}] We've received your request",
        message=(
            f"Hi {ticket.requester},\n\n"
            f"Your ticket '{ticket.subject}' has been created and is now open.\n"
            f"We'll get back to you shortly."
        ),
        to_email=ticket.requester.email,
    )


def notify_ticket_assigned(ticket):
    if not ticket.assigned_agent:
        return
    _send_email(
        subject=f"[Ticket #{ticket.id}] Assigned to you",
        message=f"Ticket '{ticket.subject}' from {ticket.company.name} has been assigned to you.",
        to_email=ticket.assigned_agent.email,
    )


def notify_ticket_status_changed(ticket, previous_status):
    _send_email(
        subject=f"[Ticket #{ticket.id}] Status updated: {ticket.get_status_display()}",
        message=(
            f"Hi {ticket.requester},\n\n"
            f"Your ticket '{ticket.subject}' changed from {previous_status} to "
            f"{ticket.status}."
        ),
        to_email=ticket.requester.email,
    )


def notify_sla_breach(ticket):
    if ticket.assigned_agent:
        _send_email(
            subject=f"[SLA breach] Ticket #{ticket.id}",
            message=f"Ticket '{ticket.subject}' ({ticket.company.name}) has breached its SLA.",
            to_email=ticket.assigned_agent.email,
        )
