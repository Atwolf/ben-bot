# Third-party imports
from django.conf import settings
from django.db import models
from nautobot.core.models.generics import BaseModel


class ChatMessage(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_messages"
    )
    message = models.TextField()
    response = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)

    # AI-specific fields
    ai_provider = models.CharField(
        max_length=50,
        blank=True,
        help_text="AI provider used (e.g., 'openai', 'anthropic', 'generic')",
    )
    ai_model = models.CharField(
        max_length=100, blank=True, help_text="AI model used for response generation"
    )
    context_used = models.JSONField(
        default=dict, blank=True, help_text="RAG context sources and metadata"
    )
    tools_executed = models.JSONField(
        default=list, blank=True, help_text="MCP tools executed during response"
    )
    response_metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional response metadata (usage, confidence, etc.)"
    )

    # Performance metrics
    response_time_ms = models.IntegerField(
        null=True, blank=True, help_text="Response generation time in milliseconds"
    )
    tokens_used = models.IntegerField(
        null=True, blank=True, help_text="Number of tokens used (if available)"
    )
    confidence_score = models.FloatField(
        null=True, blank=True, help_text="Response confidence score (0.0-1.0)"
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["session_id", "timestamp"]),
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["ai_provider", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}..."

    @property
    def has_ai_response(self):
        """Check if this message was generated using AI."""
        return bool(self.ai_provider)

    @property
    def has_tools(self):
        """Check if MCP tools were used for this response."""
        return bool(self.tools_executed)

    @property
    def has_context(self):
        """Check if RAG context was used for this response."""
        return bool(self.context_used)


class ChatSession(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-last_activity"]

    def __str__(self):
        return f"Session {self.session_id} - {self.user.username}"
