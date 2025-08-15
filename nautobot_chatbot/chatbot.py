import re
from datetime import datetime


class ChatbotEngine:
    """Simple rule-based chatbot for Nautobot assistance"""
    
    def __init__(self):
        self.responses = {
            'greeting': [
                "Hello! I'm Ben Bot, your Nautobot assistant. How can I help you today?",
                "Hi there! I'm here to help with your Nautobot questions.",
                "Greetings! What can I assist you with in Nautobot?"
            ],
            'help': [
                "I can help you with Nautobot navigation, device management, IPAM, circuits, and general questions.",
                "I'm here to assist with Nautobot features like device inventory, IP address management, and circuit tracking.",
                "Ask me about Nautobot functionality - devices, sites, racks, cables, IP addresses, and more!"
            ],
            'devices': [
                "In Nautobot, you can manage devices through the Devices section. You can add, edit, and organize network devices by site, rack, and device type.",
                "Device management in Nautobot includes tracking device types, roles, platforms, and their physical connections.",
                "To work with devices, navigate to Organization > Devices in the main menu."
            ],
            'ipam': [
                "Nautobot's IPAM features help you manage IP addresses, prefixes, VLANs, and VRFs.",
                "For IP address management, check out the IPAM section where you can create and track IP ranges, assignments, and network hierarchies.",
                "IPAM in Nautobot supports prefix allocation, IP address tracking, and VLAN management."
            ],
            'circuits': [
                "Circuit management in Nautobot helps track provider circuits, circuit types, and terminations.",
                "You can manage circuits through the Circuits section, including provider information and circuit termination points.",
                "Circuits in Nautobot can be linked to devices and interfaces for complete connectivity tracking."
            ],
            'default': [
                "I'm not sure about that specific topic. Could you ask about devices, IPAM, circuits, or general Nautobot navigation?",
                "That's an interesting question! For detailed technical help, you might want to check the Nautobot documentation.",
                "I'm still learning! Try asking about common Nautobot features like devices, IP management, or circuits."
            ]
        }
        
        self.patterns = {
            'greeting': r'\b(hi|hello|hey|greetings)\b',
            'help': r'\b(help|assist|what can you do)\b',
            'devices': r'\b(device|router|switch|server|equipment)\b',
            'ipam': r'\b(ip|address|subnet|prefix|vlan|ipam)\b',
            'circuits': r'\b(circuit|provider|connection|link)\b',
        }
    
    def generate_response(self, message, user=None):
        """Generate a response based on the user message"""
        message_lower = message.lower()
        
        # Check for patterns
        for category, pattern in self.patterns.items():
            if re.search(pattern, message_lower):
                import random
                return random.choice(self.responses[category])
        
        # Default response if no pattern matches
        import random
        response = random.choice(self.responses['default'])
        
        # Add personalization if user is available
        if user and user.first_name:
            response = f"Hi {user.first_name}! {response}"
        
        return response