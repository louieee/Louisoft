from django.urls import path
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from channels.routing import ProtocolTypeRouter
from Anonymous.consumers import ChatConsumer

application = ProtocolTypeRouter({
    'websocket': AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([
        
            path('consult/chat/<name>', ChatConsumer),
        
    ])))
})