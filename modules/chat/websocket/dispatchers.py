from base.constants import WebSocket

CLIENT_EVENT_HANDLERS = {
    WebSocket.ClientEvent.Message.SEND_MESSAGE: "handle_send_message",
    WebSocket.ClientEvent.Message.MESSAGE_DELIVERED: "handle_message_delivered",
    WebSocket.ClientEvent.Acknowledgment.ACK: "handle_acknowledgment",
}

SERVER_EVENT_HANDLERS = {
    WebSocket.ServerEvent.Message.MESSAGE: "handle_new_message",
    WebSocket.ServerEvent.Message.MESSAGE_DELIVERED: "notify_sender_message_delivered",
    WebSocket.ServerEvent.Message.MESSAGE_PINNED: "notify_message_pinned",
    WebSocket.ServerEvent.Message.MESSAGE_UNPINNED: "notify_message_unpinned",
    WebSocket.ServerEvent.Message.MESSAGE_DELETED_FOR_EVERYONE: "notify_message_deleted_for_everyone",
    WebSocket.ServerEvent.Message.REACTION_UPDATED: "notify_reaction_updated",
}
