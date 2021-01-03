from django.urls import path

from Anonymous.views import *
from Anonymous.views import _404, enter_the_chat

urlpatterns = [
    path('chat/<name>', chat, name="chat"),
    path('chats', chats, name="chats"),
    path('enter', enter_the_chat, name="enter_chat"),
    path('store', store_room, name="storeroom"),
    path('checkout', show_order, name="checkout"),
    path('invalid/<reason>', _404, name="404"),
    path('logistics', logistics, name="logistics"),
    path('', home, name="anonymous_home"),
    path('payment', redirect_payment, name="payment"),
    path("product/<name>", show_single_product, name="product"),
    path("webhook", webhook, name="webhook"),
    path('block/<name>', block_client, name="block_client"),
    path('dismiss/<name>', dismiss_client, name="dismiss_client"),
    path('order', make_order, name="make_order"),
    path('get_details', get_details, name="get_details"),
    path('chat/<int:chat_id>/message/<int:id_>/delete', delete_message, name="delete"),
    path('order/<int:id_>', get_receipt, name="get_receipt")
]
