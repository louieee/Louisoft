from .models import Customer, Message
from django.utils.timezone import datetime as d
from django.http import JsonResponse


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
    if request.method == 'GET':
        name = str(request.GET['f_name']) + ' ' + str(request.GET['l_name'])
        email = str(request.GET['email'])
        message = str(request.GET['message'])
        status = check_user(name, email, message)
        if status is True:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status':'failed'})
