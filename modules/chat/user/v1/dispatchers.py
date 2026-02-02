from base.constants import WebSocket

CLIENT_EVENT_HANDLERS = {
    WebSocket.ClientEvent.Message.SEND_MESSAGE: "handle_send_message",
}

SERVER_EVENT_HANDLERS = {
    WebSocket.ServerEvent.Message.MESSAGE: "handle_new_message",
}
