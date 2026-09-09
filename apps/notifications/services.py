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
    # Notify support mailbox / first-line if configured via DEFAULT_FROM_EMAIL mirror
    support_inbox = getattr(settings, "SUPPORT_TEAM_EMAIL", "") or ""
    if support_inbox:
        _send_email(
            subject=f"[Ticket #{ticket.id}] New ticket — {ticket.company.name}",
            message=(
                f"New ticket from {ticket.requester} ({ticket.company.name}):\n\n"
                f"Subject: {ticket.subject}\n"
                f"Category: {ticket.category.name}\n"
                f"Priority: {ticket.priority.name}\n"
            ),
            to_email=support_inbox,
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
    _send_sms(
        getattr(ticket.requester, "phone", ""),
        f"Ticket #{ticket.id} status: {ticket.get_status_display()}",
    )


def notify_ticket_escalated(ticket, actor, reason):
    recipients = set()
    if ticket.assigned_agent and ticket.assigned_agent.email:
        recipients.add(ticket.assigned_agent.email)
    support_inbox = getattr(settings, "SUPPORT_TEAM_EMAIL", "") or ""
    if support_inbox:
        recipients.add(support_inbox)
    layer = ticket.support_layer.name if ticket.support_layer else "n/a"
    body = (
        f"Ticket #{ticket.id} '{ticket.subject}' was escalated by {actor}.\n"
        f"Layer: {layer}\n"
        f"Reason: {reason}\n"
    )
    for email in recipients:
        _send_email(subject=f"[Ticket #{ticket.id}] Escalated", message=body, to_email=email)
    if ticket.requester and ticket.requester.email:
        _send_email(
            subject=f"[Ticket #{ticket.id}] Your ticket was escalated",
            message=(
                f"Hi {ticket.requester},\n\n"
                f"Your ticket '{ticket.subject}' has been escalated for further support.\n"
                f"Reason: {reason}\n"
            ),
            to_email=ticket.requester.email,
        )


def notify_ticket_commented(ticket, comment):
    """Email requester (and assignee) on public replies; skip internal notes for clients."""
    if comment.is_internal:
        if ticket.assigned_agent and ticket.assigned_agent.email:
            _send_email(
                subject=f"[Ticket #{ticket.id}] Internal note added",
                message=f"Internal note by {comment.author}:\n\n{comment.body}",
                to_email=ticket.assigned_agent.email,
            )
        return

    author_name = str(comment.author)
    stamp = comment.created_at.strftime("%Y-%m-%d %H:%M") if comment.created_at else ""
    body = (
        f"A reply was posted on ticket #{ticket.id} '{ticket.subject}'.\n\n"
        f"From: {author_name}\n"
        f"When: {stamp}\n\n"
        f"{comment.body}\n"
    )

    if ticket.requester_id != comment.author_id and ticket.requester.email:
        _send_email(
            subject=f"[Ticket #{ticket.id}] New reply",
            message=f"Hi {ticket.requester},\n\n{body}",
            to_email=ticket.requester.email,
        )
        _send_sms(
            getattr(ticket.requester, "phone", ""),
            f"Ticket #{ticket.id}: new reply from support.",
        )

    if (
        ticket.assigned_agent
        and ticket.assigned_agent_id != comment.author_id
        and ticket.assigned_agent.email
    ):
        _send_email(
            subject=f"[Ticket #{ticket.id}] New reply",
            message=body,
            to_email=ticket.assigned_agent.email,
        )


def notify_sla_breach(ticket):
    if ticket.assigned_agent:
        _send_email(
            subject=f"[SLA breach] Ticket #{ticket.id}",
            message=f"Ticket '{ticket.subject}' ({ticket.company.name}) has breached its SLA.",
            to_email=ticket.assigned_agent.email,
        )
