from django.contrib import admin

from .models import (
    Category,
    Priority,
    SLAPolicy,
    SupportLayer,
    Ticket,
    TicketActivityLog,
    TicketAttachment,
    TicketComment,
    TicketMovement,
)


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ("author", "created_at")


class TicketActivityLogInline(admin.TabularInline):
    model = TicketActivityLog
    extra = 0
    readonly_fields = ("actor", "status_from", "status_to", "note", "created_at")
    can_delete = False


class TicketMovementInline(admin.TabularInline):
    model = TicketMovement
    extra = 0
    readonly_fields = (
        "actor",
        "movement_type",
        "from_agent",
        "to_agent",
        "from_layer",
        "to_layer",
        "reason",
        "created_at",
    )
    can_delete = False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject",
        "company",
        "status",
        "priority",
        "support_layer",
        "assigned_agent",
        "created_at",
    )
    list_filter = ("status", "company", "priority", "category", "support_layer")
    search_fields = ("subject", "description")
    inlines = [TicketCommentInline, TicketActivityLogInline, TicketMovementInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")


@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ("name", "rank")


@admin.register(SupportLayer)
class SupportLayerAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "is_active")
    filter_horizontal = ("agents",)


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ("priority", "category", "first_response_minutes", "resolution_minutes")


admin.site.register(TicketAttachment)
admin.site.register(TicketMovement)
