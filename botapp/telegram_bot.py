from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

import telebot
from telebot.apihelper import ApiTelegramException

import googletrans
import gtts
import re
import os

from .models import BotUser, Message

from .botconf import buttons as btn
from .botconf import ocr_api
from .botconf.ui_strings import UI_LANGUAGES as ui
from .botconf.ui_strings import TRANSLATE_LANGUAGES as tr_lang

bot = telebot.TeleBot(settings.BOT_TOKEN, parse_mode="HTML")

bot.remove_webhook()
bot.set_webhook(url=settings.WEBHOOK)

translator = googletrans.Translator()


#------------------------------------------------------------

for admin in settings.BOT_ADMINS:
    bot.send_message(admin, "sadsadsd:", reply_markup=btn.run_btn())

@bot.callback_query_handler(func=lambda call: call.data == "run")
def run_the_bot(call):
    try:
        if settings.BOT_IS_RUNNING == False:
            for admin in settings.BOT_ADMINS:
                bot.delete_message(admin, call.message.id)

            users = BotUser.objects.all()

            for user in users:
                try:
                    bot.send_message(user.chat_id, "Bot restarted!", reply_markup=btn.main_btn(ui=ui[user.ui_language]), disable_notification=True)
                
                except ApiTelegramException as e:
                    if e.description == "Forbidden: bot was blocked by the user":
                        Message.objects.filter(chat_id=user).delete()
                        user.user_status = "blocked"
                        user.save()

                    elif e.description == "Bad Request: chat not found":
                        user.delete()

            settings.BOT_IS_RUNNING = True

        else:
            for admin in settings.BOT_ADMINS:
                bot.delete_message(admin, call.message.id)
    except Exception as e:
        print(e)


#------------------------------------------------------------

@bot.message_handler(commands=['stats'])
def statistics(msg):
    if str(msg.chat.id) in settings.BOT_ADMINS:
        active = BotUser.objects.filter(user_status="active").count()
        blocked = BotUser.objects.filter(user_status="blocked").count()
        en = BotUser.objects.filter(ui_language="en").count()
        ru = BotUser.objects.filter(ui_language="ru").count()
        uz = BotUser.objects.filter(ui_language="uz").count()

        lang_codes = BotUser.objects.values_list("language_code", flat=True)
        lang_codes = set(lang_codes)

        text = "🌐<b>Language code:</b>\n"

        for i in lang_codes:
            text += f"  <b>{i.upper()}:</b> {BotUser.objects.filter(language_code=i).count()}\n"

        bot.send_message(
            msg.chat.id, 
            f"📊<b>Users statistics</b>\n\n" +
            f"🔸<b>Active:</b> {active}\n🔹<b>Blocked:</b> {blocked}\n" +
            f"🔰<b>Total:</b> {active+blocked}\n\n{'➖'*10}\n" + 
            f"🌐<b>UI Languages:</b>\n  <b>ENG:</b> {en}\n  <b>RUS:</b> {ru}\n  <b>UZB:</b> {uz}\n\n" +
            text,
            parse_mode="HTML"
        )


#-----------------------Decorators---------------------------

def check_user(func):
    def wrapper(msg):
        if settings.BOT_IS_RUNNING:
            try:
                user = BotUser.objects.get(chat_id=msg.from_user.id)
            except ObjectDoesNotExist as e:
                if language_code in ["en","ru","uz"]:
                    ui_lang = language_code
                elif language_code in ["ru", "uk", "be"]:
                    ui_lang = "ru"
                else:
                    ui_lang = "en"

                user = BotUser.objects.create(
                    chat_id=msg.from_user.id,
                    first_name=msg.from_user.first_name,
                    username=msg.from_user.username,
                    language_code=msg.from_user.language_code,
                    ui_language=ui_lang
                )
            
            if user.user_status == "blocked":
                user.user_status = "active"
                user.save()

            func(msg, user)

    return wrapper


def get_text(func):
    def wrapper(call, user):
        try:
            msg_config = Message.objects.get(message_id=call.message.message_id)
        except:
            bot.answer_callback_query(call.id, text="An error has occurred! Please try again!", show_alert=True)
            bot.delete_message(call.from_user.id, call.message.message_id)
        else:
            func(call, user, msg_config)

    return wrapper


#------------------------------------------------------------

@bot.message_handler(commands=['start'], chat_types="private")
@check_user
def start_message(msg, user):
    bot.send_message(msg.chat.id, ui[user.ui_language]["start_msg"], reply_markup=btn.main_btn(ui=ui[user.ui_language]))


#------------------------------------------------------------

@bot.message_handler(content_types=['text', 'photo'], chat_types="private")
@check_user
def main_message(msg, user):
    if msg.text == ui[user.ui_language]["settings_btn"]:
        bot.send_message(
            msg.chat.id,
            ui[user.ui_language]["settings_msg"],
            reply_markup=btn.settings_btn(ui=ui[user.ui_language])
        )
        bot.register_next_step_handler(msg, bot_settings)

    else:
        if msg.content_type == 'text':
            text = msg.text

        elif msg.content_type == "photo":
            bot_msg = bot.send_message(msg.from_user.id, ui[user.ui_language]["scaning_msg"])
            
            img_url = bot.get_file_url(msg.photo[-1].file_id)
            
            try:
                text = ocr_api.scan(img_url)
            except:
                text = None
            finally:
                bot.delete_message(bot_msg.chat.id, bot_msg.message_id)

        else:
            text = None

        if text != None and text != '':
            src = translator.detect(text).lang

            if type(src).__name__ == "list":
                src = src[0].lower()
            else:
                src = src.lower()

            if src != user.ui_language:
                dest = user.ui_language
            elif src == user.ui_language and src == "en":
                dest = "ru"
            else:
                dest = "en"

            bot_msg = bot.reply_to(
                msg, 
                ui[user.ui_language]["choose_lang_msg"], 
                reply_markup=btn.translate_btn(tr_lang, src, dest, ui=ui[user.ui_language])
            )

            Message.objects.update_or_create(
                message_id=bot_msg.message_id, 
                chat_id=user,
                src=src,
                dest=dest,
                message_text=text
            )
        
        else:
            bot.reply_to(msg, ui[user.ui_language]["text_not_found"])


#------------------------------------------------------------

def translate_btn_filter(call):
    if call.data in ["src", "dest", "change_lang"]:
        return True
    elif re.search("^[a-z -]{2,5}\\/[a-z -]{2,5}$", call.data):
        return True
    else:
        return False


@bot.callback_query_handler(func=translate_btn_filter)
@check_user
@get_text
def translate_message(call, user, msg_config):
    text = msg_config.message_text
    src = msg_config.src
    dest = msg_config.dest

    if call.data == "src":
        bot.edit_message_reply_markup(
            call.from_user.id,
            call.message.id,
            reply_markup=btn.lang_btn(tr_lang, hide_btn=src, btn_type=call.data, ui=ui[user.ui_language])
        )

    elif call.data == "dest":
        bot.edit_message_reply_markup(
            call.from_user.id,
            call.message.id,
            reply_markup=btn.lang_btn(tr_lang, hide_btn=dest, btn_type=call.data, ui=ui[user.ui_language])
        )

    elif call.data == "change_lang":
        msg_config.src = dest
        msg_config.dest = src
        msg_config.save()

        bot.edit_message_reply_markup(
            call.from_user.id,
            call.message.id,
            reply_markup=btn.translate_btn(tr_lang, src=msg_config.src, dest=msg_config.dest, ui=ui[user.ui_language])
        )

    elif call.data == f"{src}/{dest}":
        bot.delete_message(call.from_user.id, call.message.id)
        msg_config.delete()

        tr_text = translator.translate(text, src=src, dest=dest)

        src_lang = tr_lang[src] if src in tr_lang else googletrans.LANGUAGES[src].title()
        dest_lang = tr_lang[dest] if dest in tr_lang else googletrans.LANGUAGES[dest].title()
        
        text_list = [f"{src_lang}:\n<i>{text}</i>", f"\n{'➖'*10}\n", f"{dest_lang}:\n<i>{tr_text.text}</i>"]

        full_text = text_list[0] + text_list[1] + text_list[2]

        if len(full_text) <= 4096:
            markup = btn.text_to_speech_btn(tr_lang, src=src, dest=dest) if len(text) <= 1024 else None
            
            bot.send_message(call.from_user.id, full_text, reply_markup=markup, disable_web_page_preview=True)
        
        elif len(text_list[0]) <= 4096 and len(text_list[2]) <= 4096:
            bot.send_message(call.from_user.id, text_list[0], disable_web_page_preview=True)

            bot.send_message(call.from_user.id, text_list[2], disable_web_page_preview=True)

        else:
            bot.send_message(call.from_user.id, ui[user.ui_language]["long_message"])

    
#------------------------------------------------------------

def lang_btn_filter(call):
    if call.data == "back":
        return True
    elif re.search("^(src|dest)-lang-[a-z -]{2,5}$", call.data):
        return True if call.data.split("-lang-")[1] in tr_lang else False
    else:
        return False

    
@bot.callback_query_handler(func=lang_btn_filter)
@check_user
@get_text
def languages(call, user, msg_config):
    text = msg_config.message_text
    src = msg_config.src
    dest = msg_config.dest

    if re.search("^(src|dest)-lang-[a-z -]{2,5}$", call.data):
        x = call.data.split("-lang-")

        src = x[1] if x[0]=="src" and x[1] in tr_lang else src
        dest = x[1] if x[0]=="dest" and x[1] in tr_lang else dest

        msg_config.src = src
        msg_config.dest = dest
        msg_config.save()

        bot.edit_message_reply_markup(
            call.from_user.id,
            call.message.id,
            reply_markup=btn.translate_btn(tr_lang, src=msg_config.src, dest=msg_config.dest, ui=ui[user.ui_language])
        )

    elif call.data == "back":
        bot.edit_message_reply_markup(
            call.from_user.id,
            call.message.id,
            reply_markup=btn.translate_btn(tr_lang, src=src, dest=dest, ui=ui[user.ui_language])
        )


#------------------------------------------------------------

def text_to_speech_filter(call):
    if re.search("^(src|dest)-voice-[a-z -]{2,5}$", call.data):
        return True
    else:
        return False


@bot.callback_query_handler(func=text_to_speech_filter)
@check_user
def text_to_speech(call, user):
    if os.path.exists("botapp/audio") == False:
        x=os.makedirs("botapp/audio")

    data = call.data.split("-voice-")

    text = call.message.text.split(f"\n{'➖'*10}\n")

    sep = tr_lang.get(data[1], googletrans.LANGUAGES[data[1]].title())
    separator = f"{sep}:\n"
    
    if data[0] == "src":
        text = text[0].split(separator)[1]

    elif data[0] == "dest":
        text = text[1].split(separator)[1]

    else:
        text = None

    if text != None:
        bot_msg = bot.send_message(call.from_user.id, ui[user.ui_language]["record_audio"])
        bot.send_chat_action(call.from_user.id, action="record_audio")
        
        output = gtts.gTTS(text=text, lang=data[1], slow=user.speech_is_slow)

        file_path = f"botapp/audio/{call.from_user.id}.ogg"
        output.save(file_path)

        bot.send_chat_action(call.from_user.id, action="upload_audio")

        with open(file_path, "rb") as voice:
            msg = bot.send_voice(call.from_user.id, reply_to_message_id=call.message.message_id, voice=voice)

        if os.path.exists(file_path):
            os.remove(file_path)

        bot.delete_message(bot_msg.chat.id, bot_msg.message_id)


#------------------------------------------------------------

@check_user
def bot_settings(msg, user):
    if msg.text == ui[user.ui_language]["audio_btn"]:
        bot.send_message(
            msg.chat.id,
            ui[user.ui_language]["audio_settings_msg"],
            reply_markup=btn.audio_set_btn(is_slow=user.speech_is_slow, ui=ui[user.ui_language])
        )
        bot.register_next_step_handler(msg, audio_settings)

    elif msg.text == ui[user.ui_language]["language_btn"]:
        bot.send_message(
            msg.chat.id,
            ui[user.ui_language]["language_settings_msg"],
            reply_markup=btn.lang_set_btn(tr_lang, ui=ui[user.ui_language])
        )
        bot.register_next_step_handler(msg, language_settings)

    elif msg.text == ui[user.ui_language]["back_btn"]:
        bot.send_message(
            msg.chat.id,
            ui[user.ui_language]["back_to_menu_msg"],
            reply_markup=btn.main_btn(ui=ui[user.ui_language])
        )

    else:
        bot.delete_message(msg.chat.id, msg.id)
        bot.register_next_step_handler(msg, bot_settings)


#------------------------------------------------------------

@check_user
def language_settings(msg, user):
    lang = {
        tr_lang["en"]: "en",
        tr_lang["ru"]: "ru",
        tr_lang["uz"]: "uz"
    }
    if msg.text in lang:
        user.ui_language = lang[msg.text]
        user.save()

        bot.send_message(
            msg.chat.id, 
            ui[user.ui_language]["installed_lang_msg"], 
            reply_markup=btn.lang_set_btn(tr_lang, ui=ui[user.ui_language])
        )
        bot.register_next_step_handler(msg, language_settings)

    elif msg.text == ui[user.ui_language]["back_btn"]:
        bot.send_message(
            msg.chat.id,
            ui[user.ui_language]["settings_msg"],
            reply_markup=btn.settings_btn(ui=ui[user.ui_language])
        )
        bot.register_next_step_handler(msg, bot_settings)

    else:
        bot.delete_message(msg.chat.id, msg.id)
        bot.register_next_step_handler(msg, language_settings)


#------------------------------------------------------------

@check_user
def audio_settings(msg, user):
    msg_text = {
        f"{ui[user.ui_language]['speech_is_slow_btn'][0]}": True,
        f"{ui[user.ui_language]['speech_is_slow_btn'][1]}": False
    }

    if msg.text in msg_text:
        user.speech_is_slow = msg_text[msg.text]
        user.save()

        bot.send_message(
            msg.chat.id,
            ui[user.ui_language]['speech_is_slow_msg'][0] if msg_text[msg.text]==True else ui[user.ui_language]['speech_is_slow_msg'][1], 
            reply_markup=btn.audio_set_btn(is_slow=user.speech_is_slow, ui=ui[user.ui_language])
        )
        bot.register_next_step_handler(msg, audio_settings)

    elif msg.text == ui[user.ui_language]["back_btn"]:
        bot.send_message(
            msg.chat.id,
            ui[user.ui_language]["settings_msg"],
            reply_markup=btn.settings_btn(ui=ui[user.ui_language])
        )
        bot.register_next_step_handler(msg, bot_settings)

    else:
        bot.delete_message(msg.chat.id, msg.id)
        bot.register_next_step_handler(msg, audio_settings)

