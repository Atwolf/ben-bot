from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json

from nautobot_chatbot.models import ChatMessage, ChatSession
from nautobot_chatbot.chatbot import ChatbotEngine


class ChatbotEngineTestCase(TestCase):
    def setUp(self):
        self.chatbot = ChatbotEngine()
        
    def test_greeting_response(self):
        response = self.chatbot.generate_response("Hello")
        self.assertIn("Hello", response)
        
    def test_device_response(self):
        response = self.chatbot.generate_response("Tell me about devices")
        self.assertIn("device", response.lower())
        
    def test_default_response(self):
        response = self.chatbot.generate_response("random question")
        self.assertIsNotNone(response)


class ChatbotViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
    def test_chat_api_authenticated(self):
        url = reverse('plugins:nautobot_chatbot:chat_api')
        data = {
            'message': 'Hello',
            'session_id': 'test_session_123'
        }
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.content)
        self.assertIn('response', response_data)
        self.assertIn('session_id', response_data)
        
    def test_chat_api_unauthenticated(self):
        self.client.logout()
        url = reverse('plugins:nautobot_chatbot:chat_api')
        data = {'message': 'Hello'}
        response = self.client.post(
            url, 
            json.dumps(data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login


class ChatModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_chat_message_creation(self):
        message = ChatMessage.objects.create(
            user=self.user,
            message="Test message",
            response="Test response",
            session_id="test_session"
        )
        self.assertEqual(message.user, self.user)
        self.assertEqual(message.message, "Test message")
        self.assertEqual(message.response, "Test response")
        
    def test_chat_session_creation(self):
        session = ChatSession.objects.create(
            user=self.user,
            session_id="test_session_123"
        )
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.session_id, "test_session_123")
        self.assertTrue(session.is_active)