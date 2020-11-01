from django.urls import path

from Anonymous.views import *
from Anonymous.views import _404, enter_the_chat

urlpatterns = [
    path('chat', chat, name="chat"),
    path('chats', chats, name="chats"),
    path('store', store_room, name="storeroom"),
    path('checkout/<order>', show_order, name="checkout"),
    path('invalid/<reason>', _404, name="404"),
    path('', home, name="anonymous_home"),
    path("product/<int:id_>", show_single_product, name="product"),
]
