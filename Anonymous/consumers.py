import asyncio
import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from django.utils.datetime_safe import datetime
from .models import Chat, Message
from .views import block, dismiss


class ChatConsumer(AsyncConsumer):
    def __init__(self, scope):
        super().__init__(scope)
        self.chat_data = {}
        self.chat = None
        self.consultant = None
        self.general = 'Anonymous'
        self.other_user = None
        self.chat_room = ''

    async def websocket_connect(self, event):
        await self.send({"type": "websocket.accept"})
        await self.channel_layer.group_add(
            self.general,
            self.channel_name
        )

    async def websocket_receive(self, event):
        self.chat_data = json.loads(event['text'])

        if self.chat_data['function'] == 'admit':
            try:
                chat_name = self.chat_data['chat_name']
                self.chat = await self.get_chat(chat_name)
                self.consultant = self.chat.consultant
                chat_room = self.chat.code
                self.chat_room = chat_room
                await self.channel_layer.group_add(
                    chat_room,
                    self.channel_name
                )
            except (Chat.DoesNotExist, AttributeError):
                pass
            self.chat_data['chat_room'] = self.chat_room
            await self.channel_layer.group_send(
                self.general,
                {"type": "send_message",
                 "data": {"data": self.chat_data, "chat": self.chat.name, "status": "Admitted"}})

        if self.chat_data['function'] == 'dismiss':
            await self.dismiss(self.chat.id)
            await self.channel_layer.group_send(
                self.general,
                {"type": "send_message",
                 "data": self.chat_data, "chat": self.chat.name, "status": "Dismissed"})
        if self.chat_data['function'] == 'message':
            self.chat_data['status'] = 'sent'
            if 'consultant' in self.chat_data:
                self.chat_data['consultant'] = True
            else:
                self.chat_data['consultant'] = False
            await self.save_message(self.chat, self.chat_data)
            del self.chat_data['datetime']
            await self.channel_layer.group_send(
                self.chat_room,
                {"type": "send_message",
                 "data": self.chat_data}
            )
        if self.chat_data['function'] == 'isDelivered':
            await self.update_status(int(self.chat_data['message_id']))
            await self.channel_layer.group_send(
                self.chat_room,
                {"type": "send_message",
                 "data": self.chat_data}
            )
        if self.chat_data['function'] in ['isTyping', 'notTyping', 'available']:
            await self.channel_layer.group_send(
                self.chat_room,
                {"type": "send_message",
                 "data": self.chat_data}
            )
        if self.chat_data['function'] == 'delete':
            await self.delete_message(int(self.chat_data['message_id']))
            await self.channel_layer.group_send(
                self.chat_room,
                {"type": "send_message", "data": self.chat_data}
            )
        if self.chat_data['function'] == 'block':
            await self.block_chat()
            await self.channel_layer.group_send(
                self.general,
                {"type": "send_message",
                 "data": self.chat_data, "chat": self.chat.name, "status": "blocked"})

    async def send_message(self, event):
        await self.send({"type": "websocket.send", "text": json.dumps(event['data'])})

    async def websocket_disconnect(self, event):
        # tell chat mate you're offline
        pass

    @database_sync_to_async
    def get_chat(self, name):
        self.chat = Chat.objects.get(name=name)
        return self.chat

    @database_sync_to_async
    def save_message(self, chat, data):
        encrypted_data = chat.encrypt(data['message'])
        chat_msg = Message.objects.create(text=encrypted_data, consultant=data['consultant'],
                                          chat=chat, send_status=Message.SENT)
        self.chat_data['message_id'] = chat_msg.id
        self.chat_data['time'] = chat_msg.__time__()
        self.chat_data['date'] = chat_msg.__date__()
        return chat_msg

    @database_sync_to_async
    def update_status(self, id_):
        msg = Message.objects.get(id=id_)
        msg.send_status = Message.DELIVERED
        msg.save()
        self.chat_data['status'] = 'delivered'
        return msg

    @database_sync_to_async
    def block_chat(self):
        block(self.chat)
        return

    @database_sync_to_async
    def delete_message(self, id_):
        msg = Message.objects.get(id=id_)
        if msg.expired() is False:
            msg.delete()
            self.chat_data['result'] = 'Deleted'
            return 'Deleted'
        self.chat_data['result'] = 'Not Deleted'
        return 'Not Deleted'

    @database_sync_to_async
    def dismiss(self):
        dismiss(self.chat)
        return
