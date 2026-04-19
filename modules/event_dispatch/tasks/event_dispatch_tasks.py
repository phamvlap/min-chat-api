from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from base.constants import WebSocket
from modules.event_dispatch.models import EventDispatch


@shared_task
def send_event_task(event_dispatch_id: str):
    from modules.chat.services import WebSocketService

    # Get the event dispatch record
    event_dispatch = EventDispatch.objects.filter(id=event_dispatch_id, deleted_at=None).first()

    # If the record doesn't exist, has already been acknowledged, or has exhausted retries, do nothing
    if not event_dispatch:
        return

    # If the event has already been acknowledged or is in a terminal state, do nothing
    if event_dispatch.is_terminal():
        return

    # Send the event to the WebSocket group
    WebSocketService().send_message(event_dispatch.group_name, event_dispatch.payload)

    # Update the event dispatch record with retry and acknowledgment details
    now = timezone.now()

    event_dispatch.status = EventDispatch.Status.SENT
    event_dispatch.retry_count += 1
    event_dispatch.last_attempted_at = now
    event_dispatch.ack_deadline_at = now + timedelta(seconds=WebSocket.ACKConfig.ACK_TIMEOUT)

    event_dispatch.save(
        update_fields=[
            "status",
            "retry_count",
            "last_attempted_at",
            "ack_deadline_at",
        ]
    )

    # Schedule a task to check for acknowledgment after the ACK timeout period
    check_acknowledgment_task.apply_async(
        args=[str(event_dispatch.id)],
        countdown=WebSocket.ACKConfig.ACK_TIMEOUT,
    )


@shared_task
def check_acknowledgment_task(event_dispatch_id: str):
    # Get the event dispatch record
    event_dispatch = EventDispatch.objects.filter(id=event_dispatch_id, deleted_at=None).first()

    # If the record doesn't exist, do nothing
    if not event_dispatch:
        return

    # If the event has already been acknowledged, do nothing
    if event_dispatch.is_acknowledged():
        return

    # If the acknowledgment deadline has not yet passed, do nothing (this can happen if the task was delayed for some reason)
    if event_dispatch.is_retry_exhausted():
        event_dispatch.status = EventDispatch.Status.FAILED
        event_dispatch.save(update_fields=["status"])
        return

    # If the acknowledgment deadline has passed and retries are still available, resend the event
    send_event_task.delay(str(event_dispatch.id))
