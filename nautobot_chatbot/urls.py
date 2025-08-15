# Third-party imports
from django.urls import path

# Local imports
from . import views

app_name = "nautobot_chatbot"

urlpatterns = [
    path("", views.ChatView.as_view(), name="chat"),
    path("api/chat/", views.chat_api, name="chat_api"),
    path("api/history/", views.chat_history, name="chat_history"),
    path("api/session/", views.get_user_session, name="get_session"),
    path("api/status/", views.ai_status, name="ai_status"),
]
