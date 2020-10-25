import json
from datetime import datetime, timezone, timedelta

from cryptography.fernet import Fernet
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
from Anonymous.util import generate_username


class Chat(models.Model):
    name = models.CharField(max_length=24, default=None)
    ip_address = models.CharField(max_length=30, default=None)
    consultant = models.ForeignKey('Anonymous.Consultant', on_delete=models.SET_NULL, default=None, null=True)
    secret = models.BinaryField(default=Fernet.generate_key())
    admitted = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)

    def encrypt(self, data):
        from cryptography.fernet import Fernet
        return Fernet(self.secret).encrypt(data.encode()).decode()

    def decrypt(self, cipher_text):
        from cryptography.fernet import Fernet
        return Fernet(self.secret).decrypt(cipher_text.encode()).decode()

    def chats(self):
        return [{'id': msg.id, 'text': self.decrypt(msg.txt), 'image': msg.__image__(),
                 'date': msg.time.strftime('%A, %b %e %Y.'),
                 'time': msg.time.strftime('%I : %M %p'),
                 'chat': self.name, "consultant": msg.consultant}
                for msg in Message.objects.filter(chat=self)]

    def unseen_messages(self, user):
        if user == 'consultant':
            return Message.objects.filter(chat=self, send_status=Message.SENT, consultant=True)
        return Message.objects.filter(chat=self, send_status=Message.SENT, consultant=False)

    def number_of_unseen_msgs(self, user):
        return self.unseen_messages(user).count()


class Message(models.Model):
    NOT_SENT, SENT, DELIVERED = range(3)
    STATUS = (("NOT_SENT", NOT_SENT), ('SENT', SENT), ("DELIVERED", DELIVERED))
    consultant = models.NullBooleanField(default=None)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, default=None)
    text = models.TextField(default=None)
    image = models.ImageField(default=None, upload_to=f'{chat.name}/message/images')
    time = models.DateTimeField(auto_now=True)
    send_status = models.PositiveSmallIntegerField(default=NOT_SENT, choices=STATUS)

    def __time__(self):
        return self.time.strftime('%I : %M %p')

    def __date__(self):
        return self.time.strftime('%A, %b %e %Y.')

    def __image__(self):
        if self.image is not None:
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
    code = models.CharField(max_length=16, default=generate_username('Consultant'))
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
    CATEGORIES = (('HEALTH', HEALTH), ("SEX", SEX), ('BODY_BUILDING', BODY_BUILDING), ('TECH', TECH))
    name = models.CharField(max_length=20, default=None)
    category = models.PositiveSmallIntegerField(default=None, choices=CATEGORIES)
    image = models.ImageField(default=None, upload_to=f'Products/Images')
    description = models.TextField(default=None)
    cost_price = models.DecimalField(default=0.00, max_digits=5, decimal_places=2)
    selling_price = models.DecimalField(default=0.00, max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name

    def profit(self):
        return self.selling_price - self.cost_price


class Order(models.Model):
    OFFLINE, ONLINE = range(2)
    MODE_OF_PAYMENT = (("OFFLINE", OFFLINE), ("ONLINE", ONLINE))
    orders = models.TextField(default={})
    paid = models.BooleanField(default=False)
    chat = models.ForeignKey('Anonymous.Chat', on_delete=models.CASCADE, default=None)
    mode_of_payment = models.PositiveSmallIntegerField(default=OFFLINE, choices=MODE_OF_PAYMENT)
    date_of_order = models.DateTimeField(auto_now=True)
    date_of_payment = models.DateTimeField(default=None)

    def total_price(self):
        orders = json.loads(self.orders)
        return sum((Product.objects.get(name=item).selling_price * orders[item] for item in self.orders))

    def total_profit(self):
        orders = json.loads(self.orders)
        return sum((Product.objects.get(name=item).profit() * orders[item] for item in self.orders))

    def receipt(self):
        orders = json.loads(self.orders)
        orders = [{"name": item, "price": Product.objects.get(name=item).selling_price,
                   "quantity": orders[item]}
                  for item in orders]
        total_prices = [{"product": item, "total": item['price'] * item['quantity']} for item in orders]
        total_price = sum((item['total'] for item in total_prices))
        return {"date": self.date_of_order.strftime('%A, %b %e %Y'),
                "time": self.date_of_order.strftime('%I : #M %p'),
                "orders": orders, "total_prices": total_prices, "total_price": total_price}


class Testimony(models.Model):
    text = models.TextField(default=None)
    date_added = models.DateTimeField(auto_now=True)
    order = models.OneToOneField('Anonymous.Order', on_delete=models.SET_NULL, default=None, null=True)