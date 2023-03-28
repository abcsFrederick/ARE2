from django.urls import re_path

from . import views

websocket_urlpatterns = [
	re_path(r'(?P<uid>[^/]+)/$', views.reportConsumer.as_asgi())
	# re_path(r'(?P<uid>[^/]+)/(?P<celeryId>[^/]+)/$', views.reportConsumer.as_asgi())
    # re_path('(?P<room_name>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
]