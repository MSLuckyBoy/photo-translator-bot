from django.db import models

class BotUser(models.Model):
	USER_STATUS_CHOICES = [
		("active", "active"),
		("deleted", "deleted"),
		("blocked", "blocked")
	]
	chat_id = models.PositiveIntegerField(unique=True)
	first_name = models.CharField(null=True, max_length=64)
	username = models.CharField(null=True, max_length=32)
	language_code = models.CharField(max_length=10)
	ui_language = models.CharField(max_length=10)
	user_status = models.CharField(max_length=10, choices=USER_STATUS_CHOICES, default="active") #active, deleted, blocked
	speech_is_slow = models.BooleanField(default=False)
	time_create = models.DateTimeField(auto_now_add=True)
	time_update = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.chat_id} [ {self.first_name} ]"

	class Meta:
		ordering = ['time_create', 'time_update']


class Message(models.Model):
	message_id = models.PositiveIntegerField(unique=True)
	chat_id = models.ForeignKey('botapp.BotUser', on_delete=models.CASCADE)
	src = models.CharField(max_length=20)
	dest = models.CharField(max_length=20)
	message_text = models.TextField(max_length=4096)
	time_create = models.DateTimeField(auto_now_add=True)
	time_update = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.message_id} | {self.chat_id}"

