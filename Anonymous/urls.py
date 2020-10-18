from django.urls import path

from Anonymous.views import chat, chats, _404

urlpatterns = [
    path('/chat', chat, name="chat"),
    path('/chats', chats, name="chats"),
    path('/404', _404, name="404")
    ]