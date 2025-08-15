from nautobot.apps.ui import NavMenuAddButton, NavMenuGroup, NavMenuItem, NavMenuTab


menu_items = (
    NavMenuTab(
        name="Chatbot",
        groups=(
            NavMenuGroup(
                name="Chat",
                items=(
                    NavMenuItem(
                        link="plugins:nautobot_chatbot:chat",
                        name="Chat Interface",
                        permissions=["nautobot_chatbot.view_chatmessage"],
                    ),
                ),
            ),
        ),
    ),
)