from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Consultant)

admin.site.register(Chat)

admin.site.register(Product)


class OrderAdmin(admin.ModelAdmin):
	model = Order
	ordering = ('-id',)

	def get_receipt(self, obj):
		return obj.receipt()

	get_receipt.short_description = 'Receipt'
	get_receipt.admin_order_field = 'receipt'


admin.site.register(Order, OrderAdmin)

admin.site.register(Message)
