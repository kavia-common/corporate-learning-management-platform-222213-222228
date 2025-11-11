from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

# PUBLIC_INTERFACE
class NotificationsConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for user-specific notifications at /ws/notifications/.

    Usage:
    - Connect with authenticated session (or JWT via header in future enhancement).
    - Receives broadcasted messages via group 'user_<id>'.
    """

    async def connect(self):
        user = self.scope.get("user") or AnonymousUser()
        if not user.is_authenticated:
            await self.close(code=4401)
            return
        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        user = self.scope.get("user") or AnonymousUser()
        if hasattr(self, "group_name") and user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notify(self, event):
        await self.send_json(event.get("payload", {}))
