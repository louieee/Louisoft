import json
from datetime import datetime

from decouple import config
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from Anonymous.models import Chat, Consultant, Product, Order, Testimonial, Message
from Anonymous.util import fetch_ip_address, generate_username, new_day, auth_paystack

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
			anon_chat.save()
			visitors.append(ip_address)
			_consultant.visitors = json.dumps(list(set(visitors)))
			_consultant.save()
			return redirect('chat', name=anon_chat.name)
		else:
			return redirect('chats')


def chat(request, name):
	if request.method == 'GET':
		user = 'client'
		if request.user.is_authenticated:
			user = 'consultant'
		try:
			chat_session = Chat.objects.get(name=name)
		except Chat.DoesNotExist:
			return redirect('404', reason=WRONG_URL)
		consultant = chat_session.consultant
		k = consultant.__dismissed__()
		if chat_session.ip_address in k:
			return redirect('404', reason=DISMISSED)
		if chat_session.ip_address in consultant.__blocked__():
			return redirect('404', reason=BLOCKED)
		chat_message = chat_session.messages(user)
		context = {"name": name, "consultant": consultant, "chat": chat_session, "messages": chat_message}
		if request.user.is_authenticated:
			context['authenticated'] = True
		return render(request, 'Louisoft/Anonymous/chat.html', context)


def chats(request):
	if request.method == 'GET' and request.user.is_authenticated:

		chats_ = Chat.objects.filter(consultant__user_id=request.user.id, admitted=True)
		chats_ = (chat.last_message('consultant') for chat in chats_)
		return render(request, 'Louisoft/Anonymous/chats.html', {"chats": chats_})
	else:
		return redirect('404', reason=WRONG_URL)


def get_chats(request):
	if request.method == 'GET':
		anon_chats = Chat.objects.all()
		return render(request, 'Louisoft/Anonymous/chats.html', {"chats": anon_chats})


def store_room(request):
	if request.method == 'GET':
		context = {}
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
			context['chat'] = chat_session
		products = None
		if category is not None:
			category = dict(Product.CATEGORIES)[category]
			products = Product.objects.filter(category=category)
		else:
			products = Product.objects.all()
		context['products'] = products
		return render(request, 'Louisoft/Anonymous/store_room.html', context)


def make_order(request):
	if request.method == 'GET':
		_orders = request.GET.get('cart', False)
		chat_id = request.GET.get('chat_name', False)
		chat = Chat.objects.filter(name=chat_id).first()
		if chat is None:
			return redirect('404', reason=NOT_ALLOWED)
		order = Order.objects.filter(chat=chat, paid=False).last()
		if order is None:
			order = Order()
			order.chat = chat

		_orders = json.loads(_orders)
		_orders = {item: _orders[item] for item in _orders if _orders[item] > 0}
		_orders = json.dumps(_orders)
		order.orders = _orders
		order.save()
		request.session['order_id'] = order.id
		return HttpResponse(order.id)


def home(request):
	testimonials = Testimonial.objects.order_by('-id').all()[:5]
	return render(request, 'Louisoft/Anonymous/home.html', {"testimonials": testimonials,
															"count": (x for x in range(1, 6))})


def logistics(request):
	order = Order.objects.get(id=request.session['order_id'])
	if request.method == 'GET':
		return render(request, 'Louisoft/Anonymous/order.html', {"order": order})
	if request.method == 'POST':
		address = request.POST.get('address', False)
		phone = request.POST.get('phone', False)
		email = request.POST.get('email', False)
		if address and phone:
			order.address = address
			order.phone = phone
			order.email = email
			order.save()
			return redirect('payment')
		return redirect('logistics')


# // integrate payment option


def show_order(request):
	if request.method == 'GET':
		context = Order.objects.get(id=request.session['order_id']).receipt()
		context['order_id'] = request.session['order_id']
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
	chat.consultant.blocked = json.dumps(blocked)
	chat.consultant.save()


def dismiss(chat):
	chat.admitted = False
	chat.save()
	dismissed = chat.consultant.__dismissed__()
	dismissed.append(chat.ip_address)
	chat.consultant.dismissed = json.dumps(dismissed)
	chat.consultant.save()


def show_single_product(request, name):
	if request.method == 'GET':
		context = {}
		if not request.user.is_authenticated:
			ip_address = fetch_ip_address(request)
			chat = Chat.objects.filter(ip_address=ip_address).first()
			if chat is None:
				return redirect('404', reason=WRONG_URL)
			context['chat'] = chat
		product = Product.objects.get(name=name)
		context['product'] = product
		return render(request, 'Louisoft/Anonymous/single.html', context)


def dismiss_client(request, name):
	if request.method == 'GET':
		chat = Chat.objects.get(name=name)
		dismiss(chat)
		return HttpResponse('dismissed', status=200)


def block_client(request, name):
	if request.method == 'GET':
		chat = Chat.objects.get(name=name)
		block(chat)
		return HttpResponse('blocked', status=200)


def webhook(request):
	response, computed_hmac = auth_paystack(request)
	if request.headers.get('X-Paystack-Signature') == computed_hmac:
		if response['event'] == 'charge.success' or response['event'] == 'transfer.success':
			order = Order.objects.filter(reference=response['data']['reference']).first()
			if order:
				order.paid = True
				order.date_of_payment = datetime.now()
				order.save()
		# notify me of payment

		if response['event'] == 'charge.failed' or response['event'] == 'transfer.failed':
			# notify customer through email and notify me too
			reason_of_failure = request.POST.get('data')['gateway_response']
		return HttpResponse('OK', status=200)


def redirect_payment(request):
	order = Order.objects.get(id=request.session['order_id'])
	if request.method == 'GET':
		return render(request, 'Louisoft/Anonymous/payment2.html')
	if request.method == 'POST':
		evidence = request.FILES.get('evidence', False)
		print(request.FILES)
		if evidence:
			order.evidence = evidence
			order.save()
			return render(request, 'Louisoft/Anonymous/payment2.html', {"saved": True})
		else:
			return redirect('payment')





def get_details(request):
	if 'order_id' in request.session and request.method == 'GET':
		order = Order.objects.get(id=request.session.get('order_id'))
		data = {'key': config('PAYSTACK_KEY'), 'email': order.email.__str__(),
				'amount': float(order.total_price()).__str__(),
				'ref': f"{order.chat.name}{order.id}"}
		data = json.dumps(data)
		return HttpResponse(data, status=200)


def delete_message(request, chat_id, id_):
	if request.method == 'GET':
		user = 'client'
		if request.user.is_authenticated:
			user = 'consultant'
		chat = Chat.objects.get(id=chat_id)
		chat.add_deleted_msg(user, id_)
		return HttpResponse('deleted')
