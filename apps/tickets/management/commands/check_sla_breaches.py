"""
Intended to run every 5-10 minutes via cron, e.g.:

    */5 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py check_sla_breaches

No Celery/Redis needed for this phase - a scheduled management command
is enough at current ticket volumes.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.notifications.services import notify_sla_breach
from apps.tickets.models import Ticket


class Command(BaseCommand):
    help = "Finds tickets that have breached their SLA and are not yet flagged, and notifies staff."

    def handle(self, *args, **options):
        now = timezone.now()
        open_statuses = [
            Ticket.Status.OPEN,
            Ticket.Status.IN_PROGRESS,
            Ticket.Status.ON_HOLD,
            Ticket.Status.REOPENED,
        ]
        candidates = Ticket.objects.filter(status__in=open_statuses).filter(
            resolution_due_at__lt=now
        )
        breached_count = 0
        for ticket in candidates.iterator():
            if ticket.is_sla_breached:
                notify_sla_breach(ticket)
                breached_count += 1

        self.stdout.write(self.style.SUCCESS(f"Checked SLA breaches: {breached_count} breach(es) notified."))
