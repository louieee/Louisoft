from django.shortcuts import redirect

from .models import Customer, Message
from django.utils.timezone import datetime as d
from django.core.mail import send_mail


# Create your views here.


def send_message(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        message = request.POST['message']
        phone = request.POST['phone']
        if not (name and email and message):
            request.session['message'] = 'Some Fields are not Filled.'
            request.session['status'] = 'danger'
            return redirect('index')
        try:
            customer = Customer.objects.get(name=name)
            try:
                Message.objects.get(content=message)
                request.session['message'] = 'Message sent already.'
                request.session['status'] = 'danger'
                return redirect('index')
            except Message.DoesNotExist:
                add_message(request, customer)

        except Customer.DoesNotExist:
            customer = Customer()
            customer.name = name
            customer.email = email
            customer.phone = phone
            customer.save()
            add_message(request, customer)
    if request.method == 'GET':
        return redirect('index')


def add_message(request, customer):
    message = Message()
    message.content = message
    message.sender = customer
    message.dateTime = d.now()
    message.save()
    request.session['message'] = 'Message Sent. We will keep in touch.'
    request.session['status'] = 'success'
    return redirect('index')
