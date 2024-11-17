from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone

class ChatSession(models.Model):
    """
    Model representing a chat session.

    Attributes:
        user (ForeignKey): A reference to the User who owns the chat session.
        session_id (UUIDField): A unique identifier for the session, generated using UUID.
        created_at (DateTimeField): The timestamp when the session was created, automatically set to the current date and time.
        name (CharField): Optional name for the chat for display (otherwise use overriden save)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_sessions")
    session_id = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now=True) 
    name = models.CharField(max_length=255, blank=True)

    # Sets default name
    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"Chat on {timezone.now().strftime('%Y-%m-%d @ %H:%M')}"
        super().save(*args, **kwargs)


    def __str__(self):
        """
        String representation of the ChatSession model.

        Returns:
            str: A string displaying the session ID and the username of the user who owns the session.
        """
        return f"Session {self.session_id} for {self.user.username}"

class ChatMessage(models.Model):
    """
    Model representing a chat message within a session.

    Attributes:
        session (ForeignKey): A reference to the ChatSession to which this message belongs.
        role (CharField): The role of the message sender, either 'human' or 'ai'.
        content (TextField): The actual content of the message.
        created_at (DateTimeField): The timestamp when the message was created, automatically set to the time of message creation.
    """
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=[('human', 'Human'), ('ai', 'AI')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        String representation of the ChatMessage model.

        Returns:
            str: A string displaying the role of the sender and the timestamp of message creation.
        """
        return f"Message by {self.role} at {self.created_at}"
