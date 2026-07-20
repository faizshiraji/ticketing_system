from django.urls import path

from .views import DashboardSummaryView, ReportsView

urlpatterns = [
    path("dashboard-summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("reports/", ReportsView.as_view(), name="reports"),
]
