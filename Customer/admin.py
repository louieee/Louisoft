from django.contrib import admin
from .models import Customer, Message, Project

# Register your models here.
admin.site.register(Customer)
admin.site.register(Message)
admin.site.register(Project)

