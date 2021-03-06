import re, ast
from io import BytesIO
import random
from typing import Optional

import SaitamaRobot.modules.sql.notes_sql as sql
from SaitamaRobot import LOGGER, JOIN_LOGGER, SUPPORT_CHAT, dispatcher, DRAGONS
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.handlers import MessageHandlerChecker
from SaitamaRobot.modules.helper_funcs.chat_status import user_admin, connection_status
from SaitamaRobot.modules.helper_funcs.misc import (build_keyboard,
                                                    revert_buttons)
from SaitamaRobot.modules.helper_funcs.msg_types import get_note_type
from SaitamaRobot.modules.helper_funcs.string_handling import escape_invalid_curly_brackets
from telegram import (MAX_MESSAGE_LENGTH, InlineKeyboardMarkup, Message,
                      ParseMode, Update, InlineKeyboardButton)
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown, mention_markdown
from telegram.ext import (CallbackContext, CommandHandler, CallbackQueryHandler,
                          Filters, MessageHandler)
from telegram.ext.dispatcher import run_async

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")
STICKER_MATCHER = re.compile(r"^###sticker(!photo)?###:")
BUTTON_MATCHER = re.compile(r"^###button(!photo)?###:(.*?)(?:\s|$)")
MYFILE_MATCHER = re.compile(r"^###file(!photo)?###:")
MYPHOTO_MATCHER = re.compile(r"^###photo(!photo)?###:")
MYAUDIO_MATCHER = re.compile(r"^###audio(!photo)?###:")
MYVOICE_MATCHER = re.compile(r"^###voice(!photo)?###:")
MYVIDEO_MATCHER = re.compile(r"^###video(!photo)?###:")
MYVIDEONOTE_MATCHER = re.compile(r"^###video_note(!photo)?###:")

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video
}


# Do not async
def get(update, context, notename, show_none=True, no_format=False):
    bot = context.bot
    chat_id = update.effective_message.chat.id
    note_chat_id = update.effective_chat.id
    note = sql.get_note(note_chat_id, notename)
    message = update.effective_message  # type: Optional[Message]

    if note:
        if MessageHandlerChecker.check_user(update.effective_user.id):
            return
        # If we're replying to a message, reply to that message (unless it's an error)
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id
        if note.is_reply:
            if JOIN_LOGGER:
                try:
                    bot.forward_message(
                        chat_id=chat_id,
                        from_chat_id=JOIN_LOGGER,
                        message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Y??nlendirilecek mesaj bulunamad??":
                        message.reply_text(
                            "Bu mesaj kaybolmu?? gibi g??r??n??yor - onu kald??raca????m "
                            "not listenizden.")
                        sql.rm_note(note_chat_id, notename)
                    else:
                        raise
            else:
                try:
                    bot.forward_message(
                        chat_id=chat_id,
                        from_chat_id=chat_id,
                        message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Y??nlendirilecek mesaj bulunamad??":
                        message.reply_text(
                            "G??r??n????e g??re bu notun orijinal g??ndereni silinmi?? "
                            "mesaj?? - ??zg??n??m! Bot y??neticinizden bir "
                            "bundan ka????nmak i??in ileti d??k??m??. Bu notu ??uradan kald??raca????m "
                            "kay??tl?? notlar??n??z.")
                        sql.rm_note(note_chat_id, notename)
                    else:
                        raise
        else:
            VALID_NOTE_FORMATTERS = [
                'first', 'last', 'fullname', 'username', 'id', 'chatname',
                'mention'
            ]
            valid_format = escape_invalid_curly_brackets(
                note.value, VALID_NOTE_FORMATTERS)
            if valid_format:
                if not no_format:
                    if '%%%' in valid_format:
                        split = valid_format.split('%%%')
                        if all(split):
                            text = random.choice(split)
                        else:
                            text = valid_format
                    else:
                        text = valid_format
                else:
                    text = valid_format
                text = text.format(
                    first=escape_markdown(message.from_user.first_name),
                    last=escape_markdown(message.from_user.last_name or
                                         message.from_user.first_name),
                    fullname=escape_markdown(
                        " ".join([
                            message.from_user.first_name, message.from_user
                            .last_name
                        ] if message.from_user.last_name else
                                 [message.from_user.first_name])),
                    username="@" + message.from_user.username
                    if message.from_user.username else mention_markdown(
                        message.from_user.id, message.from_user.first_name),
                    mention=mention_markdown(message.from_user.id,
                                             message.from_user.first_name),
                    chatname=escape_markdown(
                        message.chat.title if message.chat.type != "private"
                        else message.from_user.first_name),
                    id=message.from_user.id)
            else:
                text = ""

            keyb = []
            parseMode = ParseMode.MARKDOWN
            buttons = sql.get_buttons(note_chat_id, notename)
            if no_format:
                parseMode = None
                text += revert_buttons(buttons)
            else:
                keyb = build_keyboard(buttons)

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    bot.send_message(
                        chat_id,
                        text,
                        reply_to_message_id=reply_id,
                        parse_mode=parseMode,
                        disable_web_page_preview=True,
                        reply_markup=keyboard)
                else:
                    ENUM_FUNC_MAP[note.msgtype](
                        chat_id,
                        note.file,
                        caption=text,
                        reply_to_message_id=reply_id,
                        parse_mode=parseMode,
                        disable_web_page_preview=True,
                        reply_markup=keyboard)

            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    message.reply_text(
                        "Daha ??nce hi?? g??rmedi??im birinden bahsetmeye ??al????m????s??n gibi g??r??n??yor. Ger??ekten yaparsan "
                        "onlardan bahsetmek istiyorum, mesajlar??ndan birini bana ilet, ben de yapabilirim "
                        "onlar?? etiketlemek i??in!")
                elif FILE_MATCHER.match(note.value):
                    message.reply_text(
                        "Bu not, ba??ka bir bottan yanl????l??kla i??e aktar??lm???? bir dosyayd?? - kullanam??yorum "
                        "ona. Ger??ekten ihtiyac??n??z varsa, tekrar kaydetmeniz gerekecek. "
                        "Bu arada, onu notlar listenizden kald??raca????m.")
                    sql.rm_note(note_chat_id, notename)
                else:
                    message.reply_text(
                        "Bu not yanl???? bi??imlendirildi??i i??in g??nderilemedi. Sor "
                        f"@{SUPPORT_CHAT} nedenini ????zemezseniz!")
                    LOGGER.exception("#%s sohbetinde %s mesaj?? ayr????t??r??lamad??",
                                     notename, str(note_chat_id))
                    LOGGER.warning("Mesaj: %s", str(note.value))
        return
    elif show_none:
        message.reply_text("Bu not mevcut de??il")


@run_async
@connection_status
def cmd_get(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    if len(args) >= 2 and args[1].lower() == "noformat":
        get(update, context, args[0].lower(), show_none=True, no_format=True)
    elif len(args) >= 1:
        get(update, context, args[0].lower(), show_none=True)
    else:
        update.effective_message.reply_text("Get rekt")


@run_async
@connection_status
def hash_get(update: Update, context: CallbackContext):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:].lower()
    get(update, context, no_hash, show_none=False)


@run_async
@connection_status
def slash_get(update: Update, context: CallbackContext):
    message, chat_id = update.effective_message.text, update.effective_chat.id
    no_slash = message[1:]
    note_list = sql.get_all_chat_notes(chat_id)

    try:
        noteid = note_list[int(no_slash) - 1]
        note_name = str(noteid).strip(">").split()[1]
        get(update, context, note_name, show_none=False)
    except IndexError:
        update.effective_message.reply_text("Yanl???? Not Kimli??i ????")


@run_async
@user_admin
@connection_status
def save(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]

    note_name, text, data_type, content, buttons = get_note_type(msg)
    note_name = note_name.lower()
    if data_type is None:
        msg.reply_text("Dostum, not yok")
        return

    sql.add_note_to_db(
        chat_id, note_name, text, data_type, buttons=buttons, file=content)

    msg.reply_text(
        f"Yas! Eklendi  `{note_name}`.\nGet ile al??n /get `{note_name}`, or `#{note_name}`",
        parse_mode=ParseMode.MARKDOWN)

    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot:
        if text:
            msg.reply_text(
                "Bir bottan mesaj kaydetmeye ??al??????yorsunuz gibi g??r??n??yor. Maalesef, "
                "botlar bot mesajlar??n?? iletemez, bu y??zden tam mesaj?? kaydedemiyorum. "
                "\nElimden gelen t??m metni kaydedece??im, ancak daha fazlas??n?? istiyorsan??z, yapman??z gerekecek "
                "mesaj?? kendiniz iletin ve ard??ndan kaydedin.")
        else:
            msg.reply_text(
                "Botlar telegram biraz engelleniyor, bu da botlar??n bunu yapmas??n?? zorla??t??r??yor "
                "di??er botlarla etkile??ime gir, bu y??zden bu mesaj?? kaydedemiyorum "
                "her zaman yapt??????m gibi - iletmek ister misiniz? "
                "sonra bu yeni mesaj?? kaydediyor musunuz? Te??ekk??rler!")
        return


@run_async
@user_admin
@connection_status
def clear(update: Update, context: CallbackContext):
    args = context.args
    chat_id = update.effective_chat.id
    if len(args) >= 1:
        notename = args[0].lower()

        if sql.rm_note(chat_id, notename):
            update.effective_message.reply_text("Not ba??ar??yla kald??r??ld??.")
        else:
            update.effective_message.reply_text(
                "Bu benim veritaban??mda bir not de??il!")


@run_async
def clearall(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in DRAGONS:
        update.effective_message.reply_text(
            "Yaln??zca sohbet sahibi t??m notlar?? ayn?? anda temizleyebilir.")
    else:
        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="T??m notlar?? sil", callback_data="notes_rmall")
        ], [InlineKeyboardButton(text="Cancel", callback_data="notes_cancel")]])
        update.effective_message.reply_text(
            f"{chat.title} i??indeki T??M notlar?? temizlemek istedi??inizden emin misiniz ? Bu eylem geri al??namaz",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN)


@run_async
def clearall_btn(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = chat.get_member(query.from_user.id)
    if query.data == 'notes_rmall':
        if member.status == "creator" or query.from_user.id in DRAGONS:
            note_list = sql.get_all_chat_notes(chat.id)
            try:
                for notename in note_list:
                    note = notename.name.lower()
                    sql.rm_note(chat.id, note)
                message.edit_text("T??m notlar silindi.")
            except BadRequest:
                return

        if member.status == "administrator":
            query.answer("Bunu yaln??zca sohbetin sahibi yapabilir.")

        if member.status == "member":
            query.answer("Bunu yapmak i??in y??netici olman??z gerekir.")
    elif query.data == 'notes_cancel':
        if member.status == "creator" or query.from_user.id in DRAGONS:
            message.edit_text("T??m notlar??n temizlenmesi iptal edildi.")
            return
        if member.status == "administrator":
            query.answer("Bunu yaln??zca sohbetin sahibi yapabilir.")
        if member.status == "member":
            query.answer("Bunu yapmak i??in y??netici olman??z gerekir.")


@run_async
@connection_status
def list_notes(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    note_list = sql.get_all_chat_notes(chat_id)
    notes = len(note_list) + 1
    msg = "Get note by `/notenumber` or `#notename` \n\n  *ID*    *Note* \n"
    for note_id, note in zip(range(1, notes), note_list):
        if note_id < 10:
            note_name = f"`{note_id:2}.`  `#{(note.name.lower())}`\n"
        else:
            note_name = f"`{note_id}.`  `#{(note.name.lower())}`\n"
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(
                msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name

    if not note_list:
        try:
            update.effective_message.reply_text("Bu sohbette not yok!")
        except BadRequest:
            update.effective_message.reply_text(
                "Bu sohbette not yok!", quote=False)

    elif len(msg) != 0:
        update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def __import_data__(chat_id, data):
    failures = []
    for notename, notedata in data.get("extra", {}).items():
        match = FILE_MATCHER.match(notedata)
        matchsticker = STICKER_MATCHER.match(notedata)
        matchbtn = BUTTON_MATCHER.match(notedata)
        matchfile = MYFILE_MATCHER.match(notedata)
        matchphoto = MYPHOTO_MATCHER.match(notedata)
        matchaudio = MYAUDIO_MATCHER.match(notedata)
        matchvoice = MYVOICE_MATCHER.match(notedata)
        matchvideo = MYVIDEO_MATCHER.match(notedata)
        matchvn = MYVIDEONOTE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end():].strip()
            if notedata:
                sql.add_note_to_db(chat_id, notename[1:], notedata,
                                   sql.Types.TEXT)
        elif matchsticker:
            content = notedata[matchsticker.end():].strip()
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.STICKER,
                    file=content)
        elif matchbtn:
            parse = notedata[matchbtn.end():].strip()
            notedata = parse.split("<###button###>")[0]
            buttons = parse.split("<###button###>")[1]
            buttons = ast.literal_eval(buttons)
            if buttons:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.BUTTON_TEXT,
                    buttons=buttons,
                )
        elif matchfile:
            file = notedata[matchfile.end():].strip()
            file = file.split("<###TYPESPLIT###>")
            notedata = file[1]
            content = file[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.DOCUMENT,
                    file=content)
        elif matchphoto:
            photo = notedata[matchphoto.end():].strip()
            photo = photo.split("<###TYPESPLIT###>")
            notedata = photo[1]
            content = photo[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.PHOTO,
                    file=content)
        elif matchaudio:
            audio = notedata[matchaudio.end():].strip()
            audio = audio.split("<###TYPESPLIT###>")
            notedata = audio[1]
            content = audio[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.AUDIO,
                    file=content)
        elif matchvoice:
            voice = notedata[matchvoice.end():].strip()
            voice = voice.split("<###TYPESPLIT###>")
            notedata = voice[1]
            content = voice[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VOICE,
                    file=content)
        elif matchvideo:
            video = notedata[matchvideo.end():].strip()
            video = video.split("<###TYPESPLIT###>")
            notedata = video[1]
            content = video[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VIDEO,
                    file=content)
        elif matchvn:
            video_note = notedata[matchvn.end():].strip()
            video_note = video_note.split("<###TYPESPLIT###>")
            notedata = video_note[1]
            content = video_note[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VIDEO_NOTE,
                    file=content)
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            dispatcher.bot.send_document(
                chat_id,
                document=output,
                filename="failed_imports.txt",
                caption="Bu dosyalar / foto??raflar kaynak nedeniyle i??e aktar??lamad?? "
                "ba??ka bir bottan. Bu bir telgraf API k??s??tlamas??d??r ve olamaz "
                "ka????n??lmal??d??r. Rahats??zl??k i??in ??z??r dilerim!",
            )


def __stats__():
    return f"??? {sql.num_notes()} notes, across {sql.num_chats()} chats."


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return f"Bu sohbette `{len(notes)}` notlar?? var."


__help__ = """
 ??? `/get <notename>`*:* bu notename ile notu al
 ??? `#<notename>`*:* /get ile ayn??
 ??? `/notes` veya `/saved`*:* bu sohbette kaydedilmi?? t??m notlar?? listele
 ??? `/number` *:* Listedeki o numaran??n notunu ??ekecektir
Herhangi bir bi??imlendirme olmadan bir notun i??eri??ini geri almak istiyorsan??z,`/get <notename> noformat` kullan??n. Bu kutu \
g??ncel bir notu g??ncellerken faydal?? ol

*Yaln??zca y??neticiler:*
 ??? `/save <notename> <notedata>`*:* not edilen veriyi isim notu ile not olarak kaydeder
Standart i??aretleme ba??lant??s?? s??zdizimi kullan??larak bir nota bir d????me eklenebilir - ba??lant??n??n ba????na yaln??zca \
`buttonurl:` section, as such: `[somelink](buttonurl:example.com)`.Daha fazla bilgi i??in `/markdownhelp` i kontrol edin
 ??? `/save <notename>`*:* save the replied message as a note with name notename
 Rastgele notlar almak i??in fark yan??tlar??n?? `%%%` 'ile ay??r??n
 *??rnek:* 
 `/save notAd??
 Cevap 1
 %%%
 Cevap 2
 %%%
 Cevap 3`
 ??? `/clear <notename>`*:* bu isimle notu temizle
 ??? `/removeallnotes`*:* gruptaki t??m notlar?? kald??r??r
 *Not:* Not adlar?? b??y??k / k??????k harfe duyarl?? de??ildir ve kaydedilmeden ??nce otomatik olarak k??????k harfe d??n????t??r??l??r.

"""

__mod_name__ = "Notes"

GET_HANDLER = CommandHandler("get", cmd_get)
HASH_GET_HANDLER = MessageHandler(Filters.regex(r"^#[^\s]+"), hash_get)
SLASH_GET_HANDLER = MessageHandler(Filters.regex(r"^/\d+$"), slash_get)
SAVE_HANDLER = CommandHandler("save", save)
DELETE_HANDLER = CommandHandler("clear", clear)

LIST_HANDLER = DisableAbleCommandHandler(["notes", "saved"],
                                         list_notes,
                                         admin_ok=True)

CLEARALL = DisableAbleCommandHandler("removeallnotes", clearall)
CLEARALL_BTN = CallbackQueryHandler(clearall_btn, pattern=r"notes_.*")

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
dispatcher.add_handler(SLASH_GET_HANDLER)
dispatcher.add_handler(CLEARALL)
dispatcher.add_handler(CLEARALL_BTN)
