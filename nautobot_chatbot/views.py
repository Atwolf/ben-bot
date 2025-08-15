import json
import logging
import time
import uuid
from django.http import JsonResponse

logger = logging.getLogger(__name__)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import View
from .models import ChatMessage, ChatSession
from .chatbot import ChatbotEngine


@method_decorator(login_required, name='dispatch')
class ChatView(View):
    def get(self, request):
        return render(request, 'nautobot_chatbot/chat.html', {
            'chatbot_title': 'Ben Bot Assistant'
        })


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def chat_api(request):
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get or create chat session
        session, created = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': request.user,
                'is_active': True
            }
        )
        
        # Ensure session belongs to current user for security
        if session.user != request.user:
            return JsonResponse({'error': 'Invalid session'}, status=403)
        
        # Generate chatbot response using AI engine
        try:
            from .ai.engine import AIEngine
            ai_engine = AIEngine()
            
            # Track response time
            import time
            start_time = time.time()
            
            if ai_engine.is_configured():
                response_data = ai_engine.generate_response(message, request.user, session)
            else:
                # Fallback to original chatbot engine
                from .chatbot import ChatbotEngine
                chatbot = ChatbotEngine()
                response_text = chatbot.generate_response(message, request.user)
                response_data = {
                    'text': response_text,
                    'actions': [],
                    'tools_used': [],
                    'provider': 'rule_based',
                    'model': 'simple_rules'
                }
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
        except Exception as e:
            logger.error(f"AI engine failed, falling back to simple chatbot: {e}")
            # Fallback to original chatbot engine
            from .chatbot import ChatbotEngine
            chatbot = ChatbotEngine()
            response_text = chatbot.generate_response(message, request.user)
            response_data = {
                'text': response_text,
                'actions': [],
                'tools_used': [],
                'provider': 'rule_based_fallback',
                'model': 'simple_rules'
            }
            response_time_ms = None
        
        # Save the chat message with AI metadata
        chat_message = ChatMessage.objects.create(
            user=request.user,
            message=message,
            response=response_data.get('text', ''),
            session_id=session_id,
            ai_provider=response_data.get('provider', ''),
            ai_model=response_data.get('model', ''),
            context_used=response_data.get('context_sources', []),
            tools_executed=response_data.get('tools_used', []),
            response_metadata=response_data.get('usage', {}),
            response_time_ms=response_time_ms,
            tokens_used=response_data.get('usage', {}).get('total_tokens'),
            confidence_score=response_data.get('confidence_score')
        )
        
        # Update session activity
        session.save()
        
        return JsonResponse({
            'response': response_data.get('text', ''),
            'actions': response_data.get('actions', []),
            'data': response_data.get('data'),
            'session_id': session_id,
            'message_id': chat_message.id,
            'timestamp': chat_message.timestamp.isoformat(),
            'ai_metadata': {
                'provider': response_data.get('provider'),
                'model': response_data.get('model'),
                'tools_used': response_data.get('tools_used', []),
                'response_time_ms': response_time_ms
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def chat_history(request):
    session_id = request.GET.get('session_id')
    if session_id:
        messages = ChatMessage.objects.filter(
            user=request.user,
            session_id=session_id
        ).order_by('timestamp')[:50]
    else:
        # Get messages from user's most recent active session
        latest_session = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        
        if latest_session:
            messages = ChatMessage.objects.filter(
                user=request.user,
                session_id=latest_session.session_id
            ).order_by('timestamp')[:50]
        else:
            messages = ChatMessage.objects.filter(
                user=request.user
            ).order_by('-timestamp')[:20]
    
    history = [
        {
            'id': msg.id,
            'message': msg.message,
            'response': msg.response,
            'timestamp': msg.timestamp.isoformat(),
            'session_id': msg.session_id
        }
        for msg in messages
    ]
    
    return JsonResponse({'history': history})


@login_required
def get_user_session(request):
    """Get or create active session for the user"""
    try:
        # Get the most recent active session for the user
        session = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        
        if session:
            # Update last activity
            session.save()
            return JsonResponse({
                'session_id': session.session_id,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat()
            })
        else:
            # Create a new session
            session_id = f"user_{request.user.id}_{uuid.uuid4().hex[:8]}_{int(time.time())}"
            session = ChatSession.objects.create(
                user=request.user,
                session_id=session_id,
                is_active=True
            )
            return JsonResponse({
                'session_id': session.session_id,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat()
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def ai_status(request):
    """Get AI system status and configuration."""
    try:
        from .ai.engine import AIEngine
        ai_engine = AIEngine()
        status = ai_engine.get_system_status()
        return JsonResponse(status)
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        return JsonResponse({
            'error': str(e),
            'ai_enabled': False,
            'status': 'error'
        }, status=500)