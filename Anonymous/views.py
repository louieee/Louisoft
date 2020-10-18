import json
from datetime import datetime
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from Anonymous.models import Chat, Consultant, Product, Order
from Anonymous.util import fetch_ip_address, generate_username, new_day

DISMISSED, BLOCKED, WRONG_URL, WAIT, NOT_ALLOWED = range(5)


def _404(request, reason):
    data = ''
    if reason == DISMISSED:
        data = 'You have been dismissed. Please come tomorrow.'
    if reason == BLOCKED:
        data = 'You have been blocked and therefore cannot access the consultant again.'

    if reason == WRONG_URL:
        data = 'you have entered the wrong url'

    if reason == WAIT:
        data = 'please wait. The consultant is currently attending to some set of people.'

    if reason == NOT_ALLOWED:
        data = 'you do not have permission to be here.'
    return render(request, 'Louisoft/Anonymous/404.html', {"message": data}, status=404)


def enter_the_chat(request):
    if request.method == 'POST':
        consultant = request.POST['consultant']
        _consultant = Consultant.objects.filter(code=consultant).first()
        if _consultant is None:
            return redirect('404', reason=WRONG_URL)
        ip_address = fetch_ip_address(request)
        blocked = _consultant.__blocked__()
        if ip_address in blocked:
            return redirect('404', reason=BLOCKED)
        if new_day(_consultant.date):
            _consultant.date = datetime.now().date()
            _consultant.visitors = '[]'
            _consultant.dismissed = '[]'
            _consultant.save()
        visitors = _consultant.__visitors__()
        dismissed = _consultant.__dismissed__()
        if len(visitors) >= _consultant.limit:
            return redirect('404', reason=WAIT)
        if ip_address in dismissed:
            return redirect('404', reason=DISMISSED)
        try:
            anon_chat = Chat.objects.get(Q(ip_address=ip_address) & Q(consultant=_consultant))
        except Chat.DoesNotExist:
            anon_chat = Chat.objects.create(ip_address=ip_address,
                                            name=generate_username('Anonymous'),
                                            consultant=_consultant)

        anon_chat.admitted = True
        anon_chat.chats()
        anon_chat.save()
        visitors.append(ip_address)
        _consultant.visitors = json.dumps(visitors)
        _consultant.save()
        return redirect('chat', name=anon_chat)


def chat(request, name):
    if request.method == 'GET':
        chat_session = Chat.objects.get(name=name)
        consultant = chat_session.consultant
        if chat_session.ip_address in consultant.__dismissed__():
            return redirect('404', reason=DISMISSED)
        if chat_session.ip_address in consultant.__blocked__():
            return redirect('404', reason=BLOCKED)
        return render(request, 'Louisoft/Anonymous/chat.html', {"name": name})


def chats(request):
    if request.method == 'GET':
        return render(request, 'Louisoft/Anonymous/chats.html')


def get_chat(request):
    if request.method == 'GET':
        name = request.GET.get('name')
        try:
            anon_chat = Chat.objects.get(name=name)
            return json.dumps(anon_chat.chats())
        except Chat.DoesNotExist:
            return json.dumps({})


def get_chats(request):
    if request.method == 'GET':
        anon_chats = Chat.objects.all()
        return render(request, 'Louisoft/Anonymous/chats.html', {"chats": anon_chats})


def store_room(request):
    if request.method == 'GET':
        category = request.GET.get('category', None)
        ip_address = fetch_ip_address(request)
        try:
            chat_session = Chat.objects.get(ip_address=ip_address)
            consultant = chat_session.consultant
            if chat_session.ip_address in consultant.__dismissed__():
                return redirect('404', reason=DISMISSED)
            if chat_session.ip_address in consultant.__blocked__():
                return redirect('404', reason=BLOCKED)
        except Chat.DoesNotExist:
            return redirect('404', reson=NOT_ALLOWED)
        products = None
        if category is not None:
            category = dict(Product.CATEGORIES)[category]
            products = Product.objects.filter(category=category)
        else:
            products = Product.objects.all()
        return render(request, 'Louisoft/Anonymous/store_room.html', {"products": products})


def make_order(request):
    if request.method == 'GET':
        ip_address = fetch_ip_address(request)
        try:
            chat = Chat.objects.get(ip_address=ip_address)
            _orders = request.GET.get('orders')
            order = Order.objects.create(
                orders=json.dumps(_orders), chat=chat)
            return HttpResponse({"order_id": order.id})
        except Chat.DoesNotExist:
            return redirect('404', reason=NOT_ALLOWED)


def show_order(request, order):
    if request.method == 'GET':
        return render(request, 'Louisoft/Anonymous/checkout.html', {"order": order})


def get_receipt(request):
    if request.method == 'GET':
        order_id = request.GET.get('order_id')
        order = Order.objects.get(id=order_id)
        return json.dumps(order.receipt())


def block(chat):
    chat.blocked = True
    chat.save()
    blocked = chat.consultant.__blocked__()
    blocked.append(chat.ip_address)
    chat.consultant.blocked = blocked
    chat.consultant.save()


def dismiss(chat):
    chat.admitted = False
    chat.save()
    dismissed = chat.consultant.__dismissed__()
    dismissed.append(chat.ip_address)
    chat.consultant.dismissed = dismissed
    chat.consultant.save()
