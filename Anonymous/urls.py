from django.urls import path

from Anonymous.views import *
from Anonymous.views import _404, enter_the_chat

urlpatterns = [
    path('chat/<name>', chat, name="chat"),
    path('chats', chats, name="chats"),
    path('enter', enter_the_chat, name="enter_chat"),
    path('store', store_room, name="storeroom"),
    path('checkout/<order>', show_order, name="checkout"),
    path('invalid/<reason>', _404, name="404"),
    path('logistics/<order>', logistics, name="logistics"),
    path('', home, name="anonymous_home"),
    path("product/<int:id_>", show_single_product, name="product"),
    path('block/<name>', block_client, name="block_client"),
    path('dismiss/<name>', dismiss_client, name="dismiss_client")
]
