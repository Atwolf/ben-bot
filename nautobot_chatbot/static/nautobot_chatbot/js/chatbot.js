// Chatbot JavaScript functionality
(function() {
    'use strict';

    let sessionId = null;
    let isMinimized = false;
    let userId = null;

    // Initialize chatbot when DOM is loaded
    function initializeChatbot() {
        const chatToggle = document.getElementById('chat-toggle');
        const chatOverlay = document.getElementById('chatbot-overlay');
        const closeBtn = document.getElementById('close-chat');
        const minimizeBtn = document.getElementById('minimize-chat');
        const sendBtn = document.getElementById('chatbot-send');
        const input = document.getElementById('chatbot-input');

        // Full page chat interface elements
        const fullChatSendBtn = document.getElementById('send-button');
        const fullChatInput = document.getElementById('chat-input');

        if (chatToggle) {
            chatToggle.addEventListener('click', toggleChatOverlay);
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', closeChatOverlay);
        }

        if (minimizeBtn) {
            minimizeBtn.addEventListener('click', minimizeChatOverlay);
        }

        if (sendBtn && input) {
            sendBtn.addEventListener('click', () => sendMessage(input));
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage(input);
                }
            });
        }

        // Full page chat interface
        if (fullChatSendBtn && fullChatInput) {
            fullChatSendBtn.addEventListener('click', () => sendMessage(fullChatInput, true));
            fullChatInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage(fullChatInput, true);
                }
            });
        }

        // Initialize session with persistence
        initializeSession();
    }

    function toggleChatOverlay() {
        const chatOverlay = document.getElementById('chatbot-overlay');
        const chatToggle = document.getElementById('chat-toggle');
        
        if (chatOverlay.style.display === 'none' || !chatOverlay.style.display) {
            chatOverlay.style.display = 'flex';
            chatToggle.style.display = 'none';
            
            // Focus on input
            const input = document.getElementById('chatbot-input');
            if (input) {
                setTimeout(() => input.focus(), 100);
            }
        }
    }

    function closeChatOverlay() {
        const chatOverlay = document.getElementById('chatbot-overlay');
        const chatToggle = document.getElementById('chat-toggle');
        
        chatOverlay.style.display = 'none';
        chatToggle.style.display = 'flex';
        
        // Reset minimized state
        isMinimized = false;
        chatOverlay.classList.remove('minimized');
    }

    function minimizeChatOverlay() {
        const chatOverlay = document.getElementById('chatbot-overlay');
        
        isMinimized = !isMinimized;
        
        if (isMinimized) {
            chatOverlay.classList.add('minimized');
        } else {
            chatOverlay.classList.remove('minimized');
            // Focus on input when unminimized
            const input = document.getElementById('chatbot-input');
            if (input) {
                setTimeout(() => input.focus(), 100);
            }
        }
    }

    function sendMessage(inputElement, isFullPage = false) {
        const message = inputElement.value.trim();
        if (!message) return;

        const messagesContainer = isFullPage 
            ? document.getElementById('chat-messages')
            : document.getElementById('chatbot-messages');

        // Add user message to chat
        addMessageToChat(messagesContainer, message, true);

        // Clear input
        inputElement.value = '';

        // Show typing indicator
        showTypingIndicator(messagesContainer);

        // Send message to backend
        fetch('/plugins/chatbot/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator(messagesContainer);

            if (data.error) {
                addMessageToChat(messagesContainer, 'Sorry, I encountered an error. Please try again.', false);
            } else {
                // Handle rich AI response with actions and metadata
                addRichMessageToChat(messagesContainer, data, false);
                if (data.session_id && data.session_id !== sessionId) {
                    sessionId = data.session_id;
                    storeSessionId(sessionId);
                }
            }
        })
        .catch(error => {
            console.error('Chat error:', error);
            removeTypingIndicator(messagesContainer);
            addMessageToChat(messagesContainer, 'Sorry, I\'m having trouble connecting. Please try again later.', false);
        });
    }

    function addMessageToChat(container, message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const now = new Date();
        const timestamp = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${isUser ? '' : '<strong>Ben Bot:</strong> '}${escapeHtml(message)}
            </div>
            <div class="message-timestamp">${timestamp}</div>
        `;
        
        container.appendChild(messageDiv);
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    function addRichMessageToChat(container, responseData, isUser = false) {
        // Fall back to simple message if response is just a string
        if (typeof responseData === 'string') {
            addMessageToChat(container, responseData, isUser);
            return;
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user-message' : 'bot-message'} rich-message`;
        
        const now = new Date();
        const timestamp = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const response = responseData.response || responseData.text || '';
        const actions = responseData.actions || [];
        const aiMetadata = responseData.ai_metadata || {};
        const data = responseData.data;

        let actionsHtml = '';
        if (actions.length > 0) {
            actionsHtml = '<div class="message-actions">';
            actions.forEach(action => {
                actionsHtml += renderActionButton(action);
            });
            actionsHtml += '</div>';
        }

        let dataHtml = '';
        if (data && typeof data === 'object') {
            dataHtml = '<div class="message-data">' + renderDataContent(data) + '</div>';
        }

        let metadataHtml = '';
        if (aiMetadata.provider && aiMetadata.provider !== 'rule_based') {
            metadataHtml = `
                <div class="ai-metadata">
                    <span class="ai-provider">${escapeHtml(aiMetadata.provider || 'unknown')}</span>
                    ${aiMetadata.model ? `<span class="ai-model">${escapeHtml(aiMetadata.model)}</span>` : ''}
                    ${aiMetadata.response_time_ms ? `<span class="response-time">${aiMetadata.response_time_ms}ms</span>` : ''}
                    ${aiMetadata.tools_used && aiMetadata.tools_used.length > 0 ? 
                        `<span class="tools-used">Tools: ${aiMetadata.tools_used.join(', ')}</span>` : ''}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${isUser ? '' : '<strong>Ben Bot:</strong> '}${escapeHtml(response)}
                ${dataHtml}
                ${actionsHtml}
            </div>
            ${metadataHtml}
            <div class="message-timestamp">${timestamp}</div>
        `;
        
        container.appendChild(messageDiv);
        
        // Add event listeners for action buttons
        const actionButtons = messageDiv.querySelectorAll('.action-button');
        actionButtons.forEach(button => {
            button.addEventListener('click', handleActionClick);
        });
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    function renderActionButton(action) {
        const actionType = action.type || 'unknown';
        const actionText = action.text || action.label || 'Action';
        const actionUrl = action.url || '#';
        const actionData = JSON.stringify(action).replace(/"/g, '&quot;');

        let buttonClass = 'action-button';
        let icon = '';

        switch (actionType) {
            case 'navigate':
            case 'navigation':
                buttonClass += ' action-navigate';
                icon = '🔗';
                break;
            case 'search':
                buttonClass += ' action-search';
                icon = '🔍';
                break;
            case 'create':
                buttonClass += ' action-create';
                icon = '➕';
                break;
            case 'edit':
                buttonClass += ' action-edit';
                icon = '✏️';
                break;
            case 'delete':
                buttonClass += ' action-delete';
                icon = '🗑️';
                break;
            default:
                buttonClass += ' action-generic';
                icon = '⚡';
        }

        return `
            <button class="${buttonClass}" 
                    data-action="${escapeHtml(actionData)}" 
                    data-url="${escapeHtml(actionUrl)}"
                    title="${escapeHtml(action.description || actionText)}">
                <span class="action-icon">${icon}</span>
                <span class="action-text">${escapeHtml(actionText)}</span>
            </button>
        `;
    }

    function renderDataContent(data) {
        if (Array.isArray(data)) {
            // Render array as a list
            return `
                <div class="data-list">
                    ${data.map(item => `<div class="data-item">${escapeHtml(String(item))}</div>`).join('')}
                </div>
            `;
        } else if (data.results && Array.isArray(data.results)) {
            // Render search results or API results
            return `
                <div class="search-results">
                    <div class="results-header">Found ${data.results.length} results:</div>
                    ${data.results.slice(0, 5).map(result => `
                        <div class="result-item">
                            <div class="result-title">${escapeHtml(result.name || result.title || result.display || 'Item')}</div>
                            ${result.description ? `<div class="result-description">${escapeHtml(result.description)}</div>` : ''}
                            ${result.url ? `<div class="result-url"><a href="${escapeHtml(result.url)}" target="_blank">View</a></div>` : ''}
                        </div>
                    `).join('')}
                    ${data.results.length > 5 ? `<div class="results-more">... and ${data.results.length - 5} more</div>` : ''}
                </div>
            `;
        } else if (typeof data === 'object') {
            // Render object as key-value pairs
            const entries = Object.entries(data).slice(0, 10); // Limit to 10 entries
            return `
                <div class="data-object">
                    ${entries.map(([key, value]) => `
                        <div class="data-pair">
                            <span class="data-key">${escapeHtml(key)}:</span>
                            <span class="data-value">${escapeHtml(String(value))}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        return `<div class="data-raw">${escapeHtml(String(data))}</div>`;
    }

    function handleActionClick(event) {
        const button = event.currentTarget;
        const actionData = JSON.parse(button.getAttribute('data-action'));
        const actionUrl = button.getAttribute('data-url');

        // Disable button temporarily to prevent double-clicks
        button.disabled = true;
        setTimeout(() => {
            button.disabled = false;
        }, 1000);

        switch (actionData.type) {
            case 'navigate':
            case 'navigation':
                if (actionUrl && actionUrl !== '#') {
                    window.location.href = actionUrl;
                } else if (actionData.url) {
                    window.location.href = actionData.url;
                }
                break;
                
            case 'search':
                if (actionData.query) {
                    // Trigger a new search
                    sendSearchMessage(actionData.query);
                }
                break;
                
            case 'create':
                if (actionUrl && actionUrl !== '#') {
                    window.open(actionUrl, '_blank');
                } else if (actionData.url) {
                    window.open(actionData.url, '_blank');
                }
                break;
                
            case 'external':
                if (actionData.url) {
                    window.open(actionData.url, '_blank');
                }
                break;
                
            default:
                // Generic action - try URL or show message
                if (actionUrl && actionUrl !== '#') {
                    window.location.href = actionUrl;
                } else if (actionData.url) {
                    window.location.href = actionData.url;
                } else {
                    console.log('Action clicked:', actionData);
                }
        }
    }

    function sendSearchMessage(query) {
        const inputElement = document.getElementById('chatbot-input') || document.getElementById('chat-input');
        if (inputElement) {
            inputElement.value = `search for ${query}`;
            const isFullPage = inputElement.id === 'chat-input';
            sendMessage(inputElement, isFullPage);
        }
    }

    function showTypingIndicator(container) {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <strong>Ben Bot:</strong> typing
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        container.appendChild(typingDiv);
        container.scrollTop = container.scrollHeight;
    }

    function removeTypingIndicator(container) {
        const typingIndicator = container.querySelector('#typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    function loadChatHistory() {
        if (!sessionId) return;

        fetch(`/plugins/chatbot/api/history/?session_id=${sessionId}`, {
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => {
            if (!response.ok) {
                console.warn('Chat history request failed:', response.status);
                return { history: [] }; // Return empty history for failed requests
            }
            return response.json();
        })
        .then(data => {
            if (data.history && data.history.length > 0) {
                const overlayContainer = document.getElementById('chatbot-messages');
                const fullPageContainer = document.getElementById('chat-messages');
                
                // Clear existing messages except welcome message
                if (overlayContainer) {
                    const messages = overlayContainer.querySelectorAll('.chat-message:not(.bot-message:first-child)');
                    messages.forEach(msg => msg.remove());
                }
                
                // Add history messages
                data.history.forEach(msg => {
                    if (overlayContainer) {
                        addMessageToChat(overlayContainer, msg.message, true);
                        // Use simple message for history since we don't have full response data
                        addMessageToChat(overlayContainer, msg.response, false);
                    }
                    if (fullPageContainer) {
                        addMessageToChat(fullPageContainer, msg.message, true);
                        addMessageToChat(fullPageContainer, msg.response, false);
                    }
                });
            }
        })
        .catch(error => {
            console.warn('Error loading chat history:', error);
            // Don't break the UI for chat history errors
        });
    }

    function initializeSession() {
        // Get user ID from page context (added by middleware)
        const userMetaTag = document.querySelector('meta[name="chatbot-user-id"]');
        if (userMetaTag) {
            userId = userMetaTag.getAttribute('content');
        }

        // Try to get existing session from localStorage
        sessionId = getStoredSessionId();
        
        if (sessionId) {
            // Validate session with backend and load history
            validateAndLoadSession();
        } else {
            // Get or create session from backend
            createNewSession();
        }
    }

    function validateAndLoadSession() {
        // Load chat history to validate session
        loadChatHistory();
    }

    function createNewSession() {
        // Get user's active session from backend
        fetch('/plugins/chatbot/api/session/', {
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => {
            if (!response.ok) {
                console.warn('Session API request failed:', response.status);
                throw new Error('Session API failed');
            }
            return response.json();
        })
        .then(data => {
            if (data.session_id) {
                sessionId = data.session_id;
                storeSessionId(sessionId);
                loadChatHistory();
            } else {
                // Fallback to local generation
                sessionId = generateSessionId();
                storeSessionId(sessionId);
                loadChatHistory();
            }
        })
        .catch(error => {
            console.warn('Error getting session from backend:', error);
            // Fallback to local generation
            sessionId = generateSessionId();
            storeSessionId(sessionId);
            loadChatHistory();
        });
    }

    function getStoredSessionId() {
        try {
            const stored = localStorage.getItem('nautobot_chatbot_session');
            if (stored) {
                const sessionData = JSON.parse(stored);
                // Check if session is for current user and not expired (24 hours)
                if (sessionData.userId === userId && 
                    sessionData.timestamp > Date.now() - (24 * 60 * 60 * 1000)) {
                    return sessionData.sessionId;
                }
            }
        } catch (error) {
            console.warn('Error reading session from localStorage:', error);
        }
        return null;
    }

    function storeSessionId(sessionId) {
        try {
            const sessionData = {
                sessionId: sessionId,
                userId: userId,
                timestamp: Date.now()
            };
            localStorage.setItem('nautobot_chatbot_session', JSON.stringify(sessionData));
        } catch (error) {
            console.warn('Error storing session to localStorage:', error);
        }
    }

    function generateSessionId() {
        // Generate session ID with user context for better persistence
        const userPart = userId ? `user_${userId}` : 'anonymous';
        const randomPart = Math.random().toString(36).substr(2, 9);
        const timePart = Date.now();
        return `${userPart}_${randomPart}_${timePart}`;
    }

    function getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (token) {
            return token.value;
        }
        
        // Fallback: try to get from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        return '';
    }

    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // Auto-initialize if DOM is already loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeChatbot);
    } else {
        initializeChatbot();
    }

    // Make initializeChatbot available globally
    window.initializeChatbot = initializeChatbot;
})();