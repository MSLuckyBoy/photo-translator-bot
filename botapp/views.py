from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

import telebot
from .telegram_bot import bot
from .models import BotUser

from numerize import numerize


@csrf_exempt
def handle_webhook_requests(request):
    if request.META['CONTENT_TYPE'] == 'application/json':
        json_data = request.body.decode('utf-8')
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])

        return HttpResponse(status=200)

    else:
        return HttpResponse("error")


def home_page(request):
    me = bot.get_me()

    active_users = BotUser.objects.filter(user_status="active").count()

    data = {
        "first_name": me.first_name,
        "username": me.username,
        "active_users": numerize.numerize(active_users) #1500 to 1.5K
    }

    return render(request, "botapp/home_page.html", data)