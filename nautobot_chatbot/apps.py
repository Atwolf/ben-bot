# Third-party imports
from nautobot.extras.plugins import NautobotAppConfig


class NautobotChatbotConfig(NautobotAppConfig):
    name = "nautobot_chatbot"
    verbose_name = "Nautobot Chatbot"
    description = "A chatbot overlay for Nautobot interface"
    version = "1.0.0"
    author = "Ben Bot"
    author_email = "benbot@example.com"
    base_url = "chatbot"
    required_settings = []
    default_settings = {
        "enable_chatbot": True,
        "chatbot_title": "Ben Bot Assistant",
        "max_chat_history": 50,
    }
    caching_config = {}

    def ready(self):
        super().ready()
        # Any additional setup when the app is ready
