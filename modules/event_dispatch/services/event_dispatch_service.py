from django.contrib.contenttypes.models import ContentType

from base.constants import WebSocket
from modules.event_dispatch.models import EventDispatch
from modules.event_dispatch.tasks import send_event_task
from utils.normalizer_utils import to_serializable_dict


class EventDispatchService:
    def __init__(self):
        pass

    def dispatch_event(self, entity, event_type: str, payload: dict, group_name: str) -> None:
        entity_content_type = ContentType.objects.get_for_model(entity)
        payload = {
            "type": event_type,
            **to_serializable_dict(payload),
        }

        # Create an EventDispatch record
        event_dispatch = EventDispatch.objects.create(
            entity_content_type=entity_content_type,
            entity_id=str(entity.id),
            event_type=event_type,
            payload=payload,
            group_name=group_name,
            max_retries=WebSocket.ACKConfig.MAX_RETRIES,
        )

        # Schedule the task to send the event
        send_event_task.delay(str(event_dispatch.id))
