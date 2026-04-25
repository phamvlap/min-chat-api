import datetime
from uuid import UUID

from django.utils import timezone

from base.constants import WebSocket
from modules.event_dispatch.services import EventDispatchService
from modules.user.models import User
from services.redis_service import RedisService


class PresenceService:
    def __init__(
        self,
        connection_timeout: int = 120,
        last_seen_timeout: int = 60 * 60,
        throttle_timeout: int = 60,
    ):
        self.redis_service = RedisService()

        self.connection_timeout = connection_timeout
        self.last_seen_timeout = last_seen_timeout
        self.throttle_timeout = throttle_timeout

        self.presence_prefix = "user_presence"

    def set_user_presence(self, user_id: str | UUID, connection_id: str) -> bool:
        # Check if the user was already online before adding the new connection
        was_online: bool = self.is_user_online(user_id)

        # Add the new connection
        self._add_connection(user_id, connection_id)

        # Update the user's last seen time
        self._update_last_seen(user_id)

        return not was_online

    def remove_user_presence(self, user_id: str | UUID, connection_id: str) -> bool:
        # Check if the user was online before removing the connection
        was_online: bool = self.is_user_online(user_id)

        # Remove the connection
        self._remove_connection(user_id, connection_id)

        # Check if the user just went offline after removing the connection
        just_went_offline: bool = was_online and not self.is_user_online(user_id)

        # If the user just went offline, update their last seen time in the database
        if just_went_offline:
            self._set_user_last_seen(user_id)

        return just_went_offline

    def heartbeat(self, user_id: str | UUID) -> None:
        self._refresh_connection(user_id)
        self._update_last_seen(user_id)

    def broadcast_online_status(self, user_id: str | UUID) -> None:
        user: User | None = User.objects.filter(id=user_id, deleted_at=None).first()

        if not user:
            return

        # Broadcast the user's online status to their friends and conversation members
        user_last_seen_at = user.last_seen_at if user.last_seen_at else None
        if self._get_last_seen(user_id):
            user_last_seen_at = self._get_last_seen(user_id)

        EventDispatchService().dispatch_event(
            entity=user,
            event_type=WebSocket.ServerEvent.Presence.USER_ONLINE,
            payload={
                "user_id": user_id,
                "last_seen_at": user_last_seen_at,
            },
            group_name=WebSocket.Group.USER_PRESENCE.format(user_id=user_id),
        )

    def broadcast_offline_status(self, user_id: str | UUID) -> None:
        user: User | None = User.objects.filter(id=user_id, deleted_at=None).first()

        if not user:
            return

        # Broadcast the user's offline status to their friends and conversation members
        user_last_seen_at = user.last_seen_at if user.last_seen_at else None
        if self._get_last_seen(user_id):
            user_last_seen_at = self._get_last_seen(user_id)

        EventDispatchService().dispatch_event(
            entity=user,
            event_type=WebSocket.ServerEvent.Presence.USER_OFFLINE,
            payload={
                "user_id": user_id,
                "last_seen_at": user_last_seen_at,
            },
            group_name=WebSocket.Group.USER_PRESENCE.format(user_id=user_id),
        )

    def _get_user_connections_key(self, user_id: str | UUID) -> str:
        return self.redis_service.generate_key(self.presence_prefix, user_id, "connections")

    def _get_user_connection_key(self, user_id: str | UUID) -> str:
        return self.redis_service.generate_key(self.presence_prefix, user_id, "connection")

    def _get_user_last_seen_key(self, user_id: str | UUID) -> str:
        return self.redis_service.generate_key(self.presence_prefix, user_id, "last_seen")

    def _add_connection(self, user_id: str | UUID, connection_id: str) -> None:
        # Add the connection ID to the set of active connections for the user
        self.redis_service.set_add(self._get_user_connections_key(user_id), connection_id)

        # Store the connection ID with a TTL to handle unexpected disconnects
        self.redis_service.set(
            self._get_user_connection_key(user_id),
            connection_id,
            ttl=self.connection_timeout,
        )

    def _remove_connection(self, user_id: str | UUID, connection_id: str) -> None:
        # Remove the connection ID from the set of active connections for the user
        self.redis_service.set_remove(self._get_user_connections_key(user_id), connection_id)

        # Delete the connection ID key to clean up any remaining data
        self.redis_service.delete(self._get_user_connection_key(user_id))

    def _refresh_connection(self, user_id: str | UUID) -> None:
        self.redis_service.expire(self._get_user_connection_key(user_id), self.connection_timeout)

    def is_user_online(self, user_id: str | UUID) -> bool:
        return len(self.redis_service.set_members(self._get_user_connections_key(user_id))) > 0

    def _get_last_seen(self, user_id: str | UUID) -> datetime.datetime | None:
        # Retrieve the last seen timestamp from Redis
        last_seen = self.redis_service.get(self._get_user_last_seen_key(user_id))

        # Convert the timestamp to a datetime object if it exists, otherwise return None
        return datetime.datetime.fromtimestamp(last_seen, tz=datetime.UTC) if last_seen else None

    def _update_last_seen(self, user_id: str | UUID) -> None:
        # Get the last seen time from Redis
        last_seen = self._get_last_seen(user_id)

        now = timezone.now()

        # Only update the last seen time if it has been long enough since the last update to avoid excessive writes
        if last_seen and (now - last_seen).total_seconds() < float(self.throttle_timeout):
            return

        # Store the current timestamp in Redis with a TTL to ensure it expires if the user goes offline
        self.redis_service.set(
            self._get_user_last_seen_key(user_id),
            now.timestamp(),
            ttl=self.last_seen_timeout,
        )

    def _set_user_last_seen(self, user_id: str | UUID) -> None:
        # Get the last seen time from Redis
        last_seen = self._get_last_seen(user_id)

        if not last_seen:
            return

        # Update the user's last seen time in the database
        User.objects.filter(id=user_id, deleted_at=None).update(last_seen_at=last_seen)
