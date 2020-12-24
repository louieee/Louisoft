import json
from datetime import datetime
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from Anonymous.models import Chat, Consultant, Product, Order, Testimonial, Message
from Anonymous.util import fetch_ip_address, generate_username, new_day

DISMISSED, BLOCKED, WRONG_URL, WAIT, NOT_ALLOWED = range(5)


def _404(request, reason):
	data = ''
	reason = int(reason)
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
	if request.method == 'GET':
		if not request.user.is_authenticated:
			consultant = request.GET['consultant']
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
			anon_chat = Chat.objects.filter(Q(ip_address=ip_address) & Q(consultant=_consultant)).first()
			if anon_chat is None:
				anon_chat = Chat.objects.create(ip_address=ip_address,
												name=generate_username('Anonymous'),
												consultant=_consultant)

			anon_chat.admitted = True
			anon_chat.chats()
			anon_chat.save()
			visitors.append(ip_address)
			_consultant.visitors = json.dumps(list(set(visitors)))
			_consultant.save()
			return redirect('chat', name=anon_chat.name)
		else:
			return redirect('chats')


def chat(request, name):
	if request.method == 'GET':
		try:
			chat_session = Chat.objects.get(name=name)
		except Chat.DoesNotExist:
			return redirect('404', reason=WRONG_URL)
		consultant = chat_session.consultant
		if chat_session.ip_address in consultant.__dismissed__():
			return redirect('404', reason=DISMISSED)
		if chat_session.ip_address in consultant.__blocked__():
			return redirect('404', reason=BLOCKED)
		context = {"name": name, "consultant": consultant, "chat": chat_session}
		if request.user.is_authenticated:
			context['authenticated'] = True
		return render(request, 'Louisoft/Anonymous/chat.html', context)
	if request.method == 'POST':
		message = request.POST.get('message', False)
		chat = Chat.objects.get(name=name)
		if message:
			if request.user.is_authenticated:
				consultant = True
			else:
				consultant = False
			Message.objects.create(chat=chat, text=message, consultant=consultant, send_status=Message.SENT)
			return redirect('chat', name=name)


def chats(request):
	if request.method == 'GET' and request.user.is_authenticated:

		chats = Chat.objects.filter(consultant__user_id=request.user.id, admitted=True)
		return render(request, 'Louisoft/Anonymous/chats.html', {"chats": chats})
	else:
		return redirect('404', reason=WRONG_URL)


def get_chats(request):
	if request.method == 'GET':
		anon_chats = Chat.objects.all()
		return render(request, 'Louisoft/Anonymous/chats.html', {"chats": anon_chats})


def store_room(request):
	if request.method == 'GET':
		category = request.GET.get('category', None)
		if not request.user.is_authenticated:
			ip_address = fetch_ip_address(request)
			try:
				chat_session = Chat.objects.get(ip_address=ip_address)
				consultant = chat_session.consultant
				if chat_session.ip_address in consultant.__dismissed__():
					return redirect('404', reason=DISMISSED)
				if chat_session.ip_address in consultant.__blocked__():
					return redirect('404', reason=BLOCKED)
			except Chat.DoesNotExist:
				return redirect('404', reason=NOT_ALLOWED)
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


def home(request):
	testimonials = Testimonial.objects.order_by('-id').all()[:5]
	return render(request, 'Louisoft/Anonymous/home.html', {"testimonials": testimonials,
															"count": (x for x in range(1, 6))})


def logistics(request, order):
	if request.method == 'GET':
		order = Order.objects.get(id=order)
		return render(request, 'Louisoft/Anonymous/order.html', {"order": order})


def show_order(request, order):
	if request.method == 'GET':
		context = Order.objects.get(id=order).receipt()
		return render(request, 'Louisoft/Anonymous/checkout.html', context)


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


def show_single_product(request, id_):
	product = Product.objects.get(id=id_)
	return render(request, 'Louisoft/Anonymous/single.html', {"product": product})


def dismiss_client(request, name):
	if request.method == 'GET':
		chat = Chat.objects.get(name=name)
		dismiss(chat)
		return redirect('chats')


def block_client(request, name):
	if request.method == 'GET':
		chat = Chat.objects.get(name=name)
		block(chat)
		return redirect('chats')