from datetime import timedelta

from django.db.models import Avg, Count, DateField, DurationField, ExpressionWrapper, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStaffMember
from apps.tickets.models import Ticket


class DashboardSummaryView(APIView):
    """
    Single endpoint backing the backoffice dashboard's top-level view.
    Optionally filter by ?company=<id> to see one client's numbers only.
    """

    permission_classes = [IsStaffMember]

    def get(self, request):
        qs = Ticket.objects.all()
        company_id = request.query_params.get("company")
        if company_id:
            qs = qs.filter(company_id=company_id)

        by_status = dict(qs.values("status").annotate(count=Count("id")).values_list("status", "count"))

        by_category = list(
            qs.values("category__name").annotate(count=Count("id")).order_by("-count")
        )

        resolved = qs.filter(resolved_at__isnull=False)
        resolution_duration = ExpressionWrapper(
            F("resolved_at") - F("created_at"), output_field=DurationField()
        )
        avg_resolution = resolved.aggregate(avg=Avg(resolution_duration))["avg"]

        now = timezone.now()
        open_statuses = [
            Ticket.Status.OPEN,
            Ticket.Status.IN_PROGRESS,
            Ticket.Status.ON_HOLD,
            Ticket.Status.REOPENED,
        ]
        open_qs = qs.filter(status__in=open_statuses)
        breached_count = sum(1 for t in open_qs if t.is_sla_breached)

        agent_workload = list(
            qs.filter(assigned_agent__isnull=False, status__in=open_statuses)
            .values("assigned_agent__id", "assigned_agent__first_name", "assigned_agent__last_name")
            .annotate(open_tickets=Count("id"))
            .order_by("-open_tickets")
        )

        return Response(
            {
                "generated_at": now,
                "by_status": by_status,
                "by_category": by_category,
                "avg_resolution_seconds": avg_resolution.total_seconds() if avg_resolution else None,
                "currently_open": open_qs.count(),
                "currently_sla_breached": breached_count,
                "agent_workload": agent_workload,
            }
        )


class ReportsView(APIView):
    """
    Richer analytics for the admin portal.
    Query params: company (optional), days (default 30).
    """

    permission_classes = [IsStaffMember]

    def get(self, request):
        try:
            days = max(1, min(int(request.query_params.get("days", 30)), 365))
        except (TypeError, ValueError):
            days = 30

        now = timezone.now()
        start = now - timedelta(days=days)

        qs = Ticket.objects.select_related("company")
        company_id = request.query_params.get("company")
        if company_id:
            qs = qs.filter(company_id=company_id)

        created_in_period = qs.filter(created_at__gte=start).count()
        resolved_in_period = qs.filter(resolved_at__isnull=False, resolved_at__gte=start).count()

        created_rows = (
            qs.filter(created_at__gte=start)
            .annotate(day=TruncDate("created_at", output_field=DateField()))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        resolved_rows = (
            qs.filter(resolved_at__isnull=False, resolved_at__gte=start)
            .annotate(day=TruncDate("resolved_at", output_field=DateField()))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        created_map = {row["day"].isoformat(): row["count"] for row in created_rows if row["day"]}
        resolved_map = {row["day"].isoformat(): row["count"] for row in resolved_rows if row["day"]}

        tickets_created_by_day = []
        tickets_resolved_by_day = []
        for offset in range(days):
            day = (start + timedelta(days=offset)).date()
            key = day.isoformat()
            tickets_created_by_day.append({"date": key, "count": created_map.get(key, 0)})
            tickets_resolved_by_day.append({"date": key, "count": resolved_map.get(key, 0)})

        open_statuses = [
            Ticket.Status.OPEN,
            Ticket.Status.IN_PROGRESS,
            Ticket.Status.ON_HOLD,
            Ticket.Status.REOPENED,
        ]
        open_qs = qs.filter(status__in=open_statuses)
        open_sla_breached = []
        for ticket in open_qs:
            if ticket.is_sla_breached:
                open_sla_breached.append(
                    {
                        "id": ticket.id,
                        "subject": ticket.subject,
                        "company": {
                            "id": ticket.company_id,
                            "name": ticket.company.name,
                            "short_code": ticket.company.short_code,
                        },
                        "status": ticket.status,
                        "resolution_due_at": ticket.resolution_due_at,
                    }
                )

        return Response(
            {
                "generated_at": now,
                "days": days,
                "company": int(company_id) if company_id else None,
                "created_in_period": created_in_period,
                "resolved_in_period": resolved_in_period,
                "tickets_created_by_day": tickets_created_by_day,
                "tickets_resolved_by_day": tickets_resolved_by_day,
                "open_sla_breached": open_sla_breached,
            }
        )
