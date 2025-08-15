from django.utils.deprecation import MiddlewareMixin
from django.template.loader import render_to_string
from django.conf import settings


class ChatbotOverlayMiddleware(MiddlewareMixin):
    """Middleware to inject chatbot overlay into all HTML responses"""
    
    def process_response(self, request, response):
        # Only process HTML responses for authenticated users
        if (
            response.status_code == 200 and
            'text/html' in response.get('Content-Type', '') and
            hasattr(request, 'user') and
            request.user.is_authenticated and
            not request.path.startswith('/api/') and
            not request.path.startswith('/admin/')
        ):
            try:
                # Get the response content as string
                content = response.content.decode('utf-8')
                
                # Check if this is a full HTML page (has </body> tag)
                if '</body>' in content:
                    # Render the chatbot overlay
                    overlay_html = render_to_string('nautobot_chatbot/chatbot_overlay.html', {
                        'request': request,
                        'user': request.user,
                    })
                    
                    # Add user meta tag for session persistence
                    user_meta_tag = f'<meta name="chatbot-user-id" content="{request.user.id}">\n'
                    
                    # Inject user meta tag in head and overlay before closing body tag
                    if '<head>' in content:
                        content = content.replace('<head>', f'<head>\n{user_meta_tag}')
                    elif '</head>' in content:
                        content = content.replace('</head>', f'{user_meta_tag}</head>')
                    else:
                        # Fallback: add at beginning of body
                        content = content.replace('<body', f'{user_meta_tag}<body')
                    
                    content = content.replace('</body>', f'{overlay_html}\n</body>')
                    
                    # Update the response content
                    response.content = content.encode('utf-8')
                    response['Content-Length'] = len(response.content)
                    
            except Exception as e:
                # Log the error but don't break the response
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to inject chatbot overlay: {e}")
        
        return response