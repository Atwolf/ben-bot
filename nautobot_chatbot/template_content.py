from nautobot.apps.ui import TemplateExtension


class ChatbotOverlayExtension(TemplateExtension):
    """Adds the chatbot overlay to all pages"""
    model = "extras.status"  # This ensures it appears on all pages

    def buttons(self):
        return self.render("nautobot_chatbot/chatbot_overlay.html")