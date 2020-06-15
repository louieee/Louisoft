from django.shortcuts import redirect

from .models import Customer, Message
from django.utils.timezone import datetime as d
from django.core.mail import send_mail


# Create your views here.
def save_message(message, id_):
    try:
        Message.objects.get(content=message, sender_id=id_)
        return False
    except Message.DoesNotExist:
        content = Message()
        content.sender_id = id_
        content.content = message
        content.dateTime = d.now()
        content.save()
        return True


def check_user(name, email, message):
    try:
        customer = Customer.objects.get(email=email, name=name)
        return save_message(message, customer.id)
    except Customer.DoesNotExist:
        try:
            customer = Customer.objects.get(email=email)
            return save_message(message, customer.id)
        except Customer.DoesNotExist:
            customer = Customer()
            customer.name = name
            customer.email = email
            customer.save()
            return save_message(message, customer.id)


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
                message = Message.objects.get(content=message)
                request.session['message'] = 'Message sent already.'
                request.session['status'] = 'danger'
                return redirect('index')
            except Message.DoesNotExist:
                message = Message()
                message.content = message
                message.sender = customer
                message.save()
                request.session['message'] = 'Message Sent. We will keep in touch.'
                request.session['status'] = 'success'
                return redirect('index')

        except Customer.DoesNotExist:
            customer = Customer()
            customer.name = name
            customer.email = email
            customer.phone = phone
            customer.save()
            message = Message()
            message.content = message
            message.sender = customer
            message.save()
            request.session['message'] = 'Message Sent. We will keep in touch.'
            request.session['status'] = 'success'
            return redirect('index')
