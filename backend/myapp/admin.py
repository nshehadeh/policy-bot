from django.contrib import admin
from .models import ChatSession, ChatMessage


# Register your models here.
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "session_id", "created_at")
    search_fields = ("user__username", "session_id")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "role", "content", "created_at")
    search_fields = ("session__session_id", "role", "content")
