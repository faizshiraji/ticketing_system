from datetime import datetime, time, timedelta

from django.db.models import Avg, Count, DateField, DurationField, ExpressionWrapper, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStaffMember
from apps.tickets.models import Ticket


def _parse_date_range(request):
    """
    Prefer date_from / date_to (ISO dates). Fall back to days= (default 30).
    Returns (start_dt, end_dt, meta_dict).
    """
    now = timezone.now()
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")

    if date_from or date_to:
        try:
            start_d = (
                datetime.strptime(date_from, "%Y-%m-%d").date()
                if date_from
                else (now - timedelta(days=30)).date()
            )
            end_d = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else now.date()
        except ValueError:
            start_d = (now - timedelta(days=30)).date()
            end_d = now.date()
        start = timezone.make_aware(datetime.combine(start_d, time.min))
        end = timezone.make_aware(datetime.combine(end_d, time.max))
        return start, end, {"date_from": start_d.isoformat(), "date_to": end_d.isoformat()}

    try:
        days = max(1, min(int(request.query_params.get("days", 30)), 365))
    except (TypeError, ValueError):
        days = 30
    start = now - timedelta(days=days)
    return start, now, {"days": days, "date_from": start.date().isoformat(), "date_to": now.date().isoformat()}


OPEN_STATUSES = [
    Ticket.Status.OPEN,
    Ticket.Status.RECEIVED,
    Ticket.Status.IN_PROGRESS,
    Ticket.Status.ON_HOLD,
    Ticket.Status.REOPENED,
]

SUMMARY_STATUSES = [
    Ticket.Status.OPEN,
    Ticket.Status.IN_PROGRESS,
    Ticket.Status.RESOLVED,
    Ticket.Status.CLOSED,
    Ticket.Status.REOPENED,
]


class DashboardSummaryView(APIView):
    """
    Backoffice dashboard. Optional filters: company, date_from, date_to, days.
    """

    permission_classes = [IsStaffMember]

    def get(self, request):
        qs = Ticket.objects.all()
        company_id = request.query_params.get("company")
        if company_id:
            qs = qs.filter(company_id=company_id)

        start, end, date_meta = _parse_date_range(request)
        qs = qs.filter(created_at__gte=start, created_at__lte=end)

        by_status = dict(qs.values("status").annotate(count=Count("id")).values_list("status", "count"))
        status_summary = {key: by_status.get(key, 0) for key in SUMMARY_STATUSES}
        # Also expose received for staff ops
        status_summary["received"] = by_status.get(Ticket.Status.RECEIVED, 0)

        by_category = list(
            qs.values("category__name").annotate(count=Count("id")).order_by("-count")
        )

        resolved = qs.filter(resolved_at__isnull=False)
        resolution_duration = ExpressionWrapper(
            F("resolved_at") - F("created_at"), output_field=DurationField()
        )
        avg_resolution = resolved.aggregate(avg=Avg(resolution_duration))["avg"]

        now = timezone.now()
        open_qs = qs.filter(status__in=OPEN_STATUSES)
        breached_count = sum(1 for t in open_qs if t.is_sla_breached)

        agent_workload = list(
            qs.filter(assigned_agent__isnull=False, status__in=OPEN_STATUSES)
            .values("assigned_agent__id", "assigned_agent__first_name", "assigned_agent__last_name")
            .annotate(open_tickets=Count("id"))
            .order_by("-open_tickets")
        )

        return Response(
            {
                "generated_at": now,
                **date_meta,
                "by_status": by_status,
                "status_summary": status_summary,
                "by_category": by_category,
                "avg_resolution_seconds": avg_resolution.total_seconds() if avg_resolution else None,
                "currently_open": open_qs.count(),
                "currently_sla_breached": breached_count,
                "agent_workload": agent_workload,
            }
        )


class ReportsView(APIView):
    """
    Status-wise and category-wise reports.
    Query params: company, date_from, date_to, days.
    """

    permission_classes = [IsStaffMember]

    def get(self, request):
        start, end, date_meta = _parse_date_range(request)
        now = timezone.now()

        qs = Ticket.objects.select_related("company", "category", "priority")
        company_id = request.query_params.get("company")
        if company_id:
            qs = qs.filter(company_id=company_id)

        period_qs = qs.filter(created_at__gte=start, created_at__lte=end)

        created_in_period = period_qs.count()
        resolved_in_period = qs.filter(
            resolved_at__isnull=False, resolved_at__gte=start, resolved_at__lte=end
        ).count()

        by_status = list(
            period_qs.values("status").annotate(count=Count("id")).order_by("status")
        )
        by_category = list(
            period_qs.values("category__id", "category__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        detail = [
            {
                "id": t.id,
                "subject": t.subject,
                "status": t.status,
                "category": t.category.name if t.category_id else None,
                "company": t.company.name if t.company_id else None,
                "created_at": t.created_at,
                "resolved_at": t.resolved_at,
            }
            for t in period_qs.order_by("-created_at")[:500]
        ]

        created_rows = (
            period_qs.annotate(day=TruncDate("created_at", output_field=DateField()))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        resolved_rows = (
            qs.filter(resolved_at__isnull=False, resolved_at__gte=start, resolved_at__lte=end)
            .annotate(day=TruncDate("resolved_at", output_field=DateField()))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        created_map = {row["day"].isoformat(): row["count"] for row in created_rows if row["day"]}
        resolved_map = {row["day"].isoformat(): row["count"] for row in resolved_rows if row["day"]}

        day_count = max((end.date() - start.date()).days, 0) + 1
        tickets_created_by_day = []
        tickets_resolved_by_day = []
        for offset in range(day_count):
            day = (start + timedelta(days=offset)).date()
            key = day.isoformat()
            tickets_created_by_day.append({"date": key, "count": created_map.get(key, 0)})
            tickets_resolved_by_day.append({"date": key, "count": resolved_map.get(key, 0)})

        open_qs = qs.filter(status__in=OPEN_STATUSES)
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
                **date_meta,
                "company": int(company_id) if company_id else None,
                "created_in_period": created_in_period,
                "resolved_in_period": resolved_in_period,
                "by_status": by_status,
                "by_category": by_category,
                "tickets": detail,
                "tickets_created_by_day": tickets_created_by_day,
                "tickets_resolved_by_day": tickets_resolved_by_day,
                "open_sla_breached": open_sla_breached,
            }
        )
