from emoji import UNICODE_EMOJI
from google_trans_new import LANGUAGES, google_translator
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async

from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler


@run_async
def totranslate(update: Update, context: CallbackContext):
    message = update.effective_message
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)

    try:
        if message.reply_to_message:
            args = update.effective_message.text.split(None, 1)
            if message.reply_to_message.text:
                text = message.reply_to_message.text
            elif message.reply_to_message.caption:
                text = message.reply_to_message.caption

            try:
                source_lang = args[1].split(None, 1)[0]
            except (IndexError, AttributeError):
                source_lang = "Tr"

        else:
            args = update.effective_message.text.split(None, 2)
            text = args[2]
            source_lang = args[1]

        if source_lang.count('-') == 2:
            for lang in problem_lang_code:
                if lang in source_lang:
                    if source_lang.startswith(lang):
                        dest_lang = source_lang.rsplit("-", 1)[1]
                        source_lang = source_lang.rsplit("-", 1)[0]
                    else:
                        dest_lang = source_lang.split("-", 1)[1]
                        source_lang = source_lang.split("-", 1)[0]
        elif source_lang.count('-') == 1:
            for lang in problem_lang_code:
                if lang in source_lang:
                    dest_lang = source_lang
                    source_lang = None
                    break
            if dest_lang is None:
                dest_lang = source_lang.split("-")[1]
                source_lang = source_lang.split("-")[0]
        else:
            dest_lang = source_lang
            source_lang = None

        exclude_list = UNICODE_EMOJI.keys()
        for emoji in exclude_list:
            if emoji in text:
                text = text.replace(emoji, '')

        trl = google_translator()
        if source_lang is None:
            detection = trl.detect(text)
            trans_str = trl.translate(text, lang_tgt=dest_lang)
            return message.reply_text(
                f"alg??lama `{detection[0]}` dan `{dest_lang}`:\n`{trans_str}`" e ??evrildi,
                parse_mode=ParseMode.MARKDOWN)
        else:
            trans_str = trl.translate(
                text, lang_tgt=dest_lang, lang_src=source_lang)
            message.reply_text(
                f"??eviren `{source_lang}` to `{dest_lang}`:\n`{trans_str}`" ,
                parse_mode=ParseMode.MARKDOWN)

    except IndexError:
        update.effective_message.reply_text(
            "??stenen dile ??evirmek i??in di??er dillerden mesajlar?? yan??tlay??n veya mesaj yaz??n\n\n"
            "??rnek: `/tr en-ml` ??ngilizceden Malayalamca'ya ??evirmek i??in\n"
            "Veya:otomatik alg??lama ve Malayalamca ??evirmek i??in `/tr ml` .\n"
            "Dil kodlar??n??n listesi i??in bkz [Dil Kodlar?? Listesi](t.me/Poyraz2103) .",
            parse_mode="markdown",
            disable_web_page_preview=True)
    except ValueError:
        update.effective_message.reply_text(
            "Ama??lanan dil bulunamad??!")
    else:
        return


__help__ = """
??? Uzun bir mesaja yan??t olarak `/tr` or `/tl` (dil kodu)
*??rnek:* 
  `/tr en`*:* bir ??eyi ingilizceye ??evirir
  `/tr hi-en`*:* Hint??eyi ??ngilizceye ??evirir
"""

TRANSLATE_HANDLER = DisableAbleCommandHandler(["tr", "tl"], totranslate)

dispatcher.add_handler(TRANSLATE_HANDLER)

__mod_name__ = "Translator"
__command_list__ = ["tr", "tl"]
__handlers__ = [TRANSLATE_HANDLER]
