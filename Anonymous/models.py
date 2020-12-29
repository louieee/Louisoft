import json
from datetime import datetime, timezone, timedelta

from cryptography.fernet import Fernet
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
from django.db.models import Q

from Anonymous.util import generate_username


class Chat(models.Model):
	name = models.CharField(max_length=50, default=None)
	ip_address = models.CharField(max_length=30, default=None)
	consultant = models.ForeignKey('Anonymous.Consultant', on_delete=models.SET_NULL, default=None, null=True)
	secret = models.BinaryField(default=Fernet.generate_key())
	admitted = models.BooleanField(default=False)
	blocked = models.BooleanField(default=False)
	deleted_msg = models.TextField(default=json.dumps({"consultant": [], "client": []}))


	def encrypt(self, data):
		from cryptography.fernet import Fernet
		return Fernet(self.secret).encrypt(data.encode()).decode()

	def decrypt(self, cipher_text):
		from cryptography.fernet import Fernet, InvalidToken
		try:
			return Fernet(self.secret).decrypt(cipher_text.encode()).decode()
		except InvalidToken:
			return cipher_text

	def number_of_unseen_msgs(self):
		return Message.objects.filter(Q(chat=self) & Q(consultant=False) & Q(send_status=Message.SENT)).count()

	def deleted_msgs(self, user):
		data = json.loads(self.deleted_msg)
		return data[user]

	def add_deleted_msg(self, user, id_):
		data = json.loads(self.deleted_msg)
		if id_ not in data[user]:
			data[user].append(id_)
		self.deleted_msg = json.dumps(data)
		self.save()

	def messages(self, user):
		del_msgs = self.deleted_msgs(user)
		return [msg for msg in Message.objects.filter(chat=self) if msg.id not in del_msgs]

	def last_message(self, user):
		data = self.messages(user)
		data.reverse()
		if data.__len__() == 0:
			return None
		return data[0]


class Message(models.Model):
	NOT_SENT, SENT, DELIVERED = range(3)
	STATUS = ((NOT_SENT, 'NOT_SENT'), (SENT, 'SENT'), (DELIVERED, "DELIVERED"))
	consultant = models.NullBooleanField(default=None)
	chat = models.ForeignKey(Chat, on_delete=models.CASCADE, default=None)
	text = models.TextField(default=None)
	image = models.ImageField(default=None, upload_to=f'{chat.name}/message/images', null=True, blank=True)
	time = models.DateTimeField(auto_now=True)
	send_status = models.PositiveSmallIntegerField(default=NOT_SENT, choices=STATUS)

	def status(self):
		return dict(self.STATUS)[self.send_status]

	def __time__(self):
		return self.time.strftime('%I : %M %p')

	def __date__(self):
		return self.time.strftime('%A, %b %e %Y.')

	def __image__(self):
		if self.image:
			return self.image.url
		return None

	def expired(self):
		if (datetime.now(timezone.utc) - self.time) > timedelta(seconds=180):
			return True
		return False

	def decrypted_text(self):
		return self.chat.decrypt(self.text)


class Consultant(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, default=None)
	code = models.CharField(max_length=32, default=generate_username('Consultant'))
	date = models.DateField(default=None)
	limit = models.PositiveIntegerField(default=0)
	visitors = models.TextField(default='[]')
	dismissed = models.TextField(default='[]')
	blocked = models.TextField(default='[]')

	def __visitors__(self):
		return json.loads(self.visitors)

	def __dismissed__(self):
		return json.loads(self.dismissed)

	def __blocked__(self):
		return json.loads(self.blocked)


class Product(models.Model):
	HEALTH, SEX, BODY_BUILDING, TECH = range(4)
	CATEGORIES = ((HEALTH, 'HEALTH'), (SEX, 'SEX'), (BODY_BUILDING, 'BODY_BUILDING'), (TECH, 'TECH'))
	name = models.CharField(max_length=20, default=None)
	category = models.PositiveSmallIntegerField(default=None, choices=CATEGORIES)
	image = models.ImageField(default=None, upload_to=f'Products/Images')
	description = models.TextField(default=None)
	cost_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
	selling_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)

	def __str__(self):
		return self.name

	def profit(self):
		return self.selling_price - self.cost_price


class Order(models.Model):
	OFFLINE, ONLINE = range(2)
	MODE_OF_PAYMENT = ((OFFLINE, 'OFFLINE'), (ONLINE, 'ONLINE'))
	orders = models.TextField(default='{}')
	paid = models.BooleanField(default=False)
	chat = models.ForeignKey('Anonymous.Chat', on_delete=models.CASCADE, default=None)
	mode_of_payment = models.PositiveSmallIntegerField(default=OFFLINE, choices=MODE_OF_PAYMENT)
	address = models.CharField(default='', max_length=225)
	phone = models.CharField(default=None, max_length=15, null=True)
	email = models.EmailField(default=None, null=True, blank=True)
	date_of_order = models.DateTimeField(auto_now=True)
	date_of_payment = models.DateTimeField(default=None, null=True, blank=True)
	evidence = models.ImageField(upload_to='Evidence', default=None, blank=True, null=True)

	def total_price(self):
		orders = json.loads(self.orders)
		return sum((Product.objects.get(name=item).selling_price * int(orders[item]) for item in orders))

	def total_profit(self):
		orders = json.loads(self.orders)
		return sum((Product.objects.get(name=item).profit() * orders[item] for item in orders))

	def receipt(self):
		orders = json.loads(self.orders)
		name = [item for item in orders]
		quantity = [orders[item] for item in orders]
		selling_price = [Product.objects.get(name=item).selling_price for item in orders]
		total_price = [a * b for a, b in zip(selling_price, quantity)]
		row = zip(name, quantity, selling_price, total_price)
		grand_total_price = sum(total_price)
		return {"date": self.date_of_order.strftime('%A, %b %e %Y'), "time": self.date_of_order.strftime('%I : #M %p'),
				"rows": row, "grand_total": grand_total_price, "no_of_products": len(orders)}


class Testimonial(models.Model):
	name = models.CharField(max_length=30, default='Anonymous')
	text = models.TextField(default=None)
	date_added = models.DateTimeField(auto_now=True)
	order = models.OneToOneField('Anonymous.Order', on_delete=models.SET_NULL, default=None, null=True)

	def date(self):
		return self.date_added.strftime('%A, %b %e %Y')
