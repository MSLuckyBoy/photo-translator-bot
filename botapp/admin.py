from django.contrib import admin

from .models import BotUser, Message

admin.site.site_title = "@PhotoTranslator_Bot"
admin.site.site_header = "@PhotoTranslator_Bot"

@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):
	list_display = ('id', 'chat_id', 'first_name', 'username', 'language_code', 'ui_language', 'user_status', 'speech_is_slow', 'time_create', 'time_update')
	list_display_links = ('id', 'chat_id')
	search_fields = ('chat_id', 'first_name', 'username')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ('id', 'message_id', 'chat_id', 'src', 'dest', 'message_text', 'time_create', 'time_update')
	list_display_links = ('id', 'message_id')
	search_fields = ('message_id', 'message_text', 'chat_id')
