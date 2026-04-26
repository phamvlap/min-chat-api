import uuid
from typing import cast

import orjson
from asgiref.sync import async_to_sync

from base.constants import WebSocket
from base.consumers import BaseWebsocketConsumer
from base.permission import IsWebsocketUser
from modules.user.websocket.dispatchers import CLIENT_EVENT_HANDLERS, SERVER_EVENT_HANDLERS


class UserPresenceConsumer(BaseWebsocketConsumer):
    permission_classes = (IsWebsocketUser,)
    client_event_handlers = CLIENT_EVENT_HANDLERS
    server_event_handlers = SERVER_EVENT_HANDLERS

    def __init__(self, *args, **kwargs):
        from modules.user.services import PresenceService

        super().__init__(*args, **kwargs)

        self.user = None
        # Use channel name as a unique connection ID for the user
        self.connection_id = str(uuid.uuid4())
        self.subcribed_presence_groups = set()
        self.presence_service = PresenceService()

    def connect(self):
        from modules.chat.services import ConversationMemberService
        from modules.friend.services import FriendService
        from modules.user.models import User

        # Check permissions
        if not self.check_permissions(self.scope):
            self.close()
            return

        # Assign current user
        if not self.scope["user"]:
            self.close()
            return

        self.user = cast(User, self.scope["user"])

        # Add the channel to the user group
        async_to_sync(self.channel_layer.group_add)(
            WebSocket.Group.USER.format(user_id=self.user.id),
            self.channel_name,
        )

        # Get friend IDs of the user
        friend_ids: set = FriendService().get_friend_ids(self.user.id)

        # Get conversation peer user IDs for the user
        member_user_ids: set = ConversationMemberService().get_conversation_peer_user_ids_for_user(
            self.user.id
        )

        # Combine friend IDs and conversation member IDs to get the set of related user IDs
        self.subcribed_presence_groups = friend_ids | member_user_ids

        # Add the channel to the presence groups of related users (friends and conversation members)
        for related_user_id in self.subcribed_presence_groups:
            async_to_sync(self.channel_layer.group_add)(
                WebSocket.Group.USER_PRESENCE.format(user_id=related_user_id),
                self.channel_name,
            )

        self.accept()

        # Set the user as online in the presence service
        just_went_online = self.presence_service.set_user_presence(self.user.id, self.connection_id)

        # If the user just went online, broadcast their online status to related users
        if just_went_online:
            self.presence_service.broadcast_online_status(self.user.id)

    def receive(self, text_data: str | None = None, bytes_data: bytes | None = None):
        data: dict = orjson.loads(text_data) if text_data else {}
        event_type: str = data["type"]

        # Dispatch the client event to the appropriate handler
        self.dispatch_client_event(event_type=event_type, data=data)

    def disconnect(self, close_code):
        # Leave the user group
        async_to_sync(self.channel_layer.group_discard)(
            WebSocket.Group.USER.format(user_id=self.user.id),
            self.channel_name,
        )

        # Unsubscribe from all presence groups
        for related_user_id in self.subcribed_presence_groups:
            async_to_sync(self.channel_layer.group_discard)(
                WebSocket.Group.USER_PRESENCE.format(user_id=related_user_id),
                self.channel_name,
            )

        # Set the user as offline in the presence service
        just_went_offline = self.presence_service.remove_user_presence(
            self.user.id,
            self.connection_id,
        )
        # If the user just went offline, broadcast their offline status to related users
        if just_went_offline:
            self.presence_service.broadcast_offline_status(self.user.id)

    def user_online(self, event):
        self.dispatch_server_event(event)

    def handle_user_online(self, event):
        self.send_message(event)

    def user_offline(self, event):
        self.dispatch_server_event(event)

    def handle_user_offline(self, event):
        self.send_message(event)

    def ping(self, event):
        self.dispatch_server_event(event)

    def pong(self, event):
        # Just update the user's presence without sending any message back to the client
        self.presence_service.heartbeat(self.user.id)
