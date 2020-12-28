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
		self.client = scope['url_route']['kwargs']['name']
		self.chat_room = self.client

	async def websocket_connect(self, event):
		self.chat = await self.get_chat(name=self.chat_room)
		await self.send({"type": "websocket.accept"})
		await self.channel_layer.group_add(
			self.chat_room,
			self.channel_name
		)

	async def websocket_receive(self, event):
		self.chat_data = json.loads(event['text'])

		if self.chat_data['function'] == 'message':
			self.chat_data['status'] = 'sent'
			print(self.chat_data['message'])
			await self.save_message(self.chat)
			await self.channel_layer.group_send(
				self.chat_room,
				{"type": "send_message", "data": self.chat_data})
		if self.chat_data['function'] == 'isDelivered':
			await self.update_status(int(self.chat_data['message_id']))
			await self.channel_layer.group_send(
				self.chat_room,
				{"type": "send_message", "data": self.chat_data})
		if self.chat_data['function'] in ['isTyping', 'NotTyping', 'available']:
			await self.channel_layer.group_send(
				self.chat_room,
				{"type": "send_message", "data": self.chat_data})
		if self.chat_data['function'] == 'delete':
			self.chat_data['result'] = await self.delete_message(int(self.chat_data['message_id']))
			await self.channel_layer.group_send(
				self.chat_room,
				{"type": "send_message", "data": self.chat_data}
			)
		if self.chat_data['function'] in ['block', 'dismiss']:
			self.chat_data['chat'] = self.chat.name
			await self.channel_layer.group_send(
				self.chat_room,
				{"type": "send_message", "data": self.chat_data})

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
	def save_message(self, chat):
		encrypted_data = chat.encrypt(self.chat_data['message'])
		consultant = self.chat_data['sender'] == 'consultant'
		chat_msg = Message.objects.create(text=encrypted_data, consultant=consultant,
										  chat=chat, send_status=Message.SENT)
		if self.chat_data['sender'] == 'consultant':
			self.chat_data['name'] = chat.consultant.code
		if self.chat_data['sender'] == 'client':
			self.chat_data['name'] = chat.name
		self.chat_data['message_id'] = chat_msg.id
		self.chat_data['expired'] = chat_msg.expired()
		self.chat_data['time'] = chat_msg.__time__()
		self.chat_data['date'] = chat_msg.__date__()
		self.chat_data['status'] = chat_msg.status()
		return chat_msg

	@database_sync_to_async
	def update_status(self, id_):
		msg = Message.objects.get(id=id_)
		msg.send_status = Message.DELIVERED
		msg.save()
		self.chat_data['status'] = 'delivered'
		return msg

	@database_sync_to_async
	def delete_message(self, id_):
		msg = Message.objects.get(id=id_)
		if msg.expired() is False:
			msg.delete()
			self.chat_data['result'] = 'Deleted'
			return 'Deleted'
		self.chat_data['result'] = 'Not Deleted'
		return 'Not Deleted'
