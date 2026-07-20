"""Ticket assignment / escalation helpers that record TicketMovement + internal notes."""

from django.db import transaction

from apps.accounts.models import User

from .models import SupportLayer, Ticket, TicketComment, TicketMovement


def lowest_active_layer() -> SupportLayer | None:
    return SupportLayer.objects.filter(is_active=True).order_by("level").first()


def next_active_layer(current: SupportLayer | None) -> SupportLayer | None:
    qs = SupportLayer.objects.filter(is_active=True).order_by("level")
    if current is None:
        return qs.first()
    return qs.filter(level__gt=current.level).first()


def highest_layer_for_user(user: User) -> SupportLayer | None:
    return user.support_layers.filter(is_active=True).order_by("-level").first()


@transaction.atomic
def record_movement(
    *,
    ticket: Ticket,
    actor: User,
    movement_type: str,
    reason: str = "",
    from_agent=None,
    to_agent=None,
    from_layer=None,
    to_layer=None,
    create_internal_comment: bool = False,
) -> TicketMovement:
    movement = TicketMovement.objects.create(
        ticket=ticket,
        actor=actor,
        movement_type=movement_type,
        from_agent=from_agent,
        to_agent=to_agent,
        from_layer=from_layer,
        to_layer=to_layer,
        reason=reason,
    )
    if create_internal_comment and reason.strip():
        label = dict(TicketMovement.MovementType.choices).get(movement_type, movement_type)
        TicketComment.objects.create(
            ticket=ticket,
            author=actor,
            body=f"[{label}] {reason.strip()}",
            is_internal=True,
        )
    return movement


@transaction.atomic
def escalate_ticket(
    *,
    ticket: Ticket,
    actor: User,
    mode: str,
    reason: str,
    target_agent_id: int | None = None,
) -> Ticket:
    from_agent = ticket.assigned_agent
    from_layer = ticket.support_layer
    reason = reason.strip()
    if not reason:
        raise ValueError("Reason is required.")

    if mode == "next":
        to_layer = next_active_layer(ticket.support_layer)
        if to_layer is None:
            raise ValueError("No higher support layer is available to escalate to.")
        ticket.support_layer = to_layer
        ticket.assigned_agent = None
        ticket.save(update_fields=["support_layer", "assigned_agent", "updated_at"])
        record_movement(
            ticket=ticket,
            actor=actor,
            movement_type=TicketMovement.MovementType.ESCALATE_NEXT,
            reason=reason,
            from_agent=from_agent,
            to_agent=None,
            from_layer=from_layer,
            to_layer=to_layer,
            create_internal_comment=True,
        )
        return ticket

    if mode == "agent":
        try:
            target = User.objects.get(pk=target_agent_id)
        except User.DoesNotExist as exc:
            raise ValueError("Target agent not found.") from exc
        if not target.is_staff_member:
            raise ValueError("Target must be a staff member.")

        to_layer = highest_layer_for_user(target) or ticket.support_layer
        ticket.assigned_agent = target
        ticket.support_layer = to_layer
        ticket.save(update_fields=["assigned_agent", "support_layer", "updated_at"])
        record_movement(
            ticket=ticket,
            actor=actor,
            movement_type=TicketMovement.MovementType.ESCALATE_AGENT,
            reason=reason,
            from_agent=from_agent,
            to_agent=target,
            from_layer=from_layer,
            to_layer=to_layer,
            create_internal_comment=True,
        )
        return ticket

    raise ValueError("Invalid escalation mode.")
