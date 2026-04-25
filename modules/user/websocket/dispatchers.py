from base.constants import WebSocket

CLIENT_EVENT_HANDLERS = {
    WebSocket.ClientEvent.Acknowledgment.ACK: "handle_acknowledgment",
}

SERVER_EVENT_HANDLERS = {
    WebSocket.ServerEvent.Presence.USER_ONLINE: "handle_user_online",
    WebSocket.ServerEvent.Presence.USER_OFFLINE: "handle_user_offline",
    WebSocket.ServerEvent.Heartbeat.PING: "pong",
}
