from channels.generic.websocket import AsyncWebsocketConsumer
import json

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "test"

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        await self.send(text_data=json.dumps({
            "message": "WebSocket connected for notifications."
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive from WebSocket client
    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({
            "message": "Mhm... it works!"
        }))
        # Optional: Handle incoming messages from frontend if needed

    # Receive from group
    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": event["type"],
            "data": event["data"]
        }))

class NewWUD(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "newWUD"

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        await self.send(text_data=json.dumps({
            "message": "Ahora sabes cuando hay datos de recuperación nuevos."
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive from WebSocket client
    async def receive(self, text_data):
        data = json.loads(text_data)
        # Optional: Handle incoming messages from frontend if needed

    # Receive from group
    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": event["type"],
            "data": event["data"]
        }))

class Alert(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "alert"

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        await self.send(text_data=json.dumps({
            "message": "Ahora sabrás cuando hay una alerta."
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive from WebSocket client
    async def receive(self, text_data):
        data = json.loads(text_data)
        # Optional: Handle incoming messages from frontend if needed

    # Receive from group
    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": event["type"],
            "data": event["data"]
        }))