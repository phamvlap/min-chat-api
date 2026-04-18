from uuid import UUID

from django.contrib.contenttypes.models import ContentType

from modules.event_dispatch.constants import ACKConfig
from modules.event_dispatch.models import EventDispatch
from modules.event_dispatch.tasks import send_event_task
from utils.normalizer_utils import to_serializable_dict


class EventDispatchService:
    def __init__(self):
        pass

    def dispatch_event(
        self,
        entity_content_type: ContentType,
        entity_id: str | UUID,
        event_type: str,
        payload: dict,
        group_name: str,
    ) -> None:
        payload = {
            "type": event_type,
            **to_serializable_dict(payload),
        }

        # Create an EventDispatch record
        event_dispatch = EventDispatch.objects.create(
            entity_content_type=entity_content_type,
            entity_id=entity_id,
            event_type=event_type,
            payload=payload,
            group_name=group_name,
            max_retries=ACKConfig.MAX_RETRIES,
        )

        # Schedule the task to send the event
        send_event_task.delay(str(event_dispatch.id))
