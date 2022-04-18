from telebot import types
import googletrans
import gtts


def run_btn():
	markup = types.InlineKeyboardMarkup()
	markup.add(
		types.InlineKeyboardButton(text="RUN", callback_data="run")
	)
	return markup


def translate_btn(data, src, dest, ui):
	src_text = data[src] if src in data else googletrans.LANGUAGES[src].title()
	dest_text = data[dest] if dest in data else googletrans.LANGUAGES[dest].title()
	
	markup = types.InlineKeyboardMarkup()
	markup.add(
		types.InlineKeyboardButton(text=src_text, callback_data="src"),
		types.InlineKeyboardButton(text="🔁", callback_data="change_lang"),
		types.InlineKeyboardButton(text=dest_text, callback_data="dest")
	)
	markup.add(
		types.InlineKeyboardButton(text=ui["translate_ibtn"], callback_data=f"{src}/{dest}")
	)

	return markup


def lang_btn(data, hide_btn, btn_type, ui):
	btn = []
	markup = types.InlineKeyboardMarkup()

	for key, value in data.items():
		if key == hide_btn:
			continue
		btn.append(types.InlineKeyboardButton(text=value, callback_data=f"{btn_type}-lang-{key}"))

	markup.add(*btn)
	markup.add(
		types.InlineKeyboardButton(text=ui["back_btn"], callback_data='back')
	)

	return markup


def text_to_speech_btn(data, src=None, dest=None):
	markup = types.InlineKeyboardMarkup()
	
	langs = gtts.lang.tts_langs()

	if src in langs and dest in langs:
		src_text = data.get(src, googletrans.LANGUAGES[src].title())
		dest_text =  data.get(dest, googletrans.LANGUAGES[dest].title())
		markup.add(
			types.InlineKeyboardButton(text=f"🔈 {src_text}", callback_data=f"src-voice-{src}"),
			types.InlineKeyboardButton(text=f"🔈 {dest_text}", callback_data=f"dest-voice-{dest}")
		)
	elif src in langs:
		src_text = data.get(src, googletrans.LANGUAGES[src].title())
		markup.add(
			types.InlineKeyboardButton(text=f"🔈 {src_text}", callback_data=f"src-voice-{src}")
		)
	elif dest in langs:
		dest_text =  data.get(dest, googletrans.LANGUAGES[dest].title())
		markup.add(
			types.InlineKeyboardButton(text=f"🔈 {dest_text}", callback_data=f"dest-voice-{dest}")
		)
	else:
		markup = None

	return markup


def main_btn(ui):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
	markup.add(
		types.KeyboardButton(text=ui["settings_btn"])
	)
	return markup


def settings_btn(ui):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
	markup.add(
		types.KeyboardButton(text=ui["audio_btn"]),
		types.KeyboardButton(text=ui["language_btn"])
	)
	markup.add(
		types.KeyboardButton(text=ui["back_btn"])
	)
	return markup


def audio_set_btn(is_slow, ui):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
	markup.add(
		types.KeyboardButton(text=f"{ui['speech_is_slow_btn'][is_slow]}")
	)
	markup.add(
		types.KeyboardButton(text=ui["back_btn"])
	)
	return markup


def lang_set_btn(data, ui):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
	markup.add(
		types.KeyboardButton(text=data["en"]),
		types.KeyboardButton(text=data["ru"]),
		types.KeyboardButton(text=data["uz"])
	)
	markup.add(
		types.KeyboardButton(text=ui["back_btn"])
	)
	return markup

