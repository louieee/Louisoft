from django.db import models


# Create your models here.
class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.name


class Message(models.Model):
    content = models.TextField(max_length=None)
    dateTime = models.DateTimeField()
    sender = models.ForeignKey(Customer, on_delete=models.CASCADE)
