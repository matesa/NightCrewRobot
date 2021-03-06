import re
import random
from html import escape

import telegram
from telegram import ParseMode, InlineKeyboardMarkup, Message, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    DispatcherHandlerStop,
    CallbackQueryHandler,
    run_async,
    Filters,
)
from telegram.utils.helpers import mention_html, escape_markdown

from SaitamaRobot import dispatcher, LOGGER, DRAGONS
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.handlers import MessageHandlerChecker
from SaitamaRobot.modules.helper_funcs.chat_status import user_admin
from SaitamaRobot.modules.helper_funcs.extraction import extract_text
from SaitamaRobot.modules.helper_funcs.filters import CustomFilters
from SaitamaRobot.modules.helper_funcs.misc import build_keyboard_parser
from SaitamaRobot.modules.helper_funcs.msg_types import get_filter_type
from SaitamaRobot.modules.helper_funcs.string_handling import (
    split_quotes,
    button_markdown_parser,
    escape_invalid_curly_brackets,
    markdown_to_html,
)
from SaitamaRobot.modules.sql import cust_filters_sql as sql

from SaitamaRobot.modules.connection import connected

from SaitamaRobot.modules.helper_funcs.alternate import send_message, typing_action

HANDLER_GROUP = 10

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
    # sql.Types.VIDEO_NOTE.value: dispatcher.bot.send_video_note
}


@run_async
@typing_action
def list_handlers(update, context):
    chat = update.effective_chat
    user = update.effective_user

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if not conn is False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
        filter_list = "*Filtrele {}:*\n"
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "Yerel filtreler"
            filter_list = "*yerel filtreler:*\n"
        else:
            chat_name = chat.title
            filter_list = "*{} i??indeki filtreler*:\n"

    all_handlers = sql.get_chat_triggers(chat_id)

    if not all_handlers:
        send_message(update.effective_message,
                     "{} ????ine kaydedilmi?? filtre yok!".format(chat_name))
        return

    for keyword in all_handlers:
        entry = " ??? `{}`\n".format(escape_markdown(keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            send_message(
                update.effective_message,
                filter_list.format(chat_name),
                parse_mode=telegram.ParseMode.MARKDOWN,
            )
            filter_list = entry
        else:
            filter_list += entry

    send_message(
        update.effective_message,
        filter_list.format(chat_name),
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
@typing_action
def filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = msg.text.split(
        None,
        1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    conn = connected(context.bot, update, chat, user.id)
    if not conn is False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local filters"
        else:
            chat_name = chat.title

    if not msg.reply_to_message and len(args) < 2:
        send_message(
            update.effective_message,
            "L??tfen bu filtrenin yan??t vermesi i??in klavye anahtar kelimesini girin!",
        )
        return

    if msg.reply_to_message:
        if len(args) < 2:
            send_message(
                update.effective_message,
                "L??tfen bu filtrenin yan??t vermesi i??in anahtar kelime girin!",
            )
            return
        else:
            keyword = args[1]
    else:
        extracted = split_quotes(args[1])
        if len(extracted) < 1:
            return
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()

    # Add the filter
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat_id):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    text, file_type, file_id = get_filter_type(msg)
    if not msg.reply_to_message and len(extracted) >= 2:
        offset = len(extracted[1]) - len(
            msg.text)  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            extracted[1], entities=msg.parse_entities(), offset=offset)
        text = text.strip()
        if not text:
            send_message(
                update.effective_message,
                "Not mesaj?? yok - SADECE d????melere sahip olamazs??n??z, onunla birlikte gitmek i??in bir mesaja ihtiyac??n??z var!",
            )
            return

    elif msg.reply_to_message and len(args) >= 2:
        if msg.reply_to_message.text:
            text_to_parsing = msg.reply_to_message.text
        elif msg.reply_to_message.caption:
            text_to_parsing = msg.reply_to_message.caption
        else:
            text_to_parsing = ""
        offset = len(text_to_parsing
                    )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            text_to_parsing, entities=msg.parse_entities(), offset=offset)
        text = text.strip()

    elif not text and not file_type:
        send_message(
            update.effective_message,
            "L??tfen bu filtre yan??t?? i??in anahtar kelime girin!",
        )
        return

    elif msg.reply_to_message:
        if msg.reply_to_message.text:
            text_to_parsing = msg.reply_to_message.text
        elif msg.reply_to_message.caption:
            text_to_parsing = msg.reply_to_message.caption
        else:
            text_to_parsing = ""
        offset = len(text_to_parsing
                    )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            text_to_parsing, entities=msg.parse_entities(), offset=offset)
        text = text.strip()
        if (msg.reply_to_message.text or
                msg.reply_to_message.caption) and not text:
            send_message(
                update.effective_message,
                "Not mesaj?? yok - SADECE d????melere sahip olamazs??n??z, onunla birlikte gitmek i??in bir mesaja ihtiyac??n??z var!",
            )
            return

    else:
        send_message(update.effective_message, "Invalid filter!")
        return

    add = addnew_filter(update, chat_id, keyword, text, file_type, file_id,
                        buttons)
    # This is an old method
    # sql.add_filter(chat_id, keyword, content, is_sticker, is_document, is_image, is_audio, is_voice, is_video, buttons)

    if add is True:
        send_message(
            update.effective_message,
            "'{}' ????inde *{}* filtresi kaydedildi!".format(keyword, chat_name),
            parse_mode=telegram.ParseMode.MARKDOWN,
        )
    raise DispatcherHandlerStop


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
@typing_action
def stop_filter(update, context):
    chat = update.effective_chat
    user = update.effective_user
    args = update.effective_message.text.split(None, 1)

    conn = connected(context.bot, update, chat, user.id)
    if not conn is False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "Local filters"
        else:
            chat_name = chat.title

    if len(args) < 2:
        send_message(update.effective_message, "Neyi durdurmal??y??m?")
        return

    chat_filters = sql.get_chat_triggers(chat_id)

    if not chat_filters:
        send_message(update.effective_message, "Hay??r burada aktif filtreler!")
        return

    for keyword in chat_filters:
        if keyword == args[1]:
            sql.remove_filter(chat_id, args[1])
            send_message(
                update.effective_message,
                "Tamam, bu filtreyi *{}* ile yan??tlamay?? b??rakaca????m.".format(
                    chat_name),
                parse_mode=telegram.ParseMode.MARKDOWN,
            )
            raise DispatcherHandlerStop

    send_message(
        update.effective_message,
        "Bu bir filtre de??il:??u anda etkin olan filtreleri almak i??in /filters t??klay??n.",
    )


@run_async
def reply_filter(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]

    if not update.effective_user or update.effective_user.id == 777000:
        return
    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_triggers(chat.id)
    for keyword in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            if MessageHandlerChecker.check_user(update.effective_user.id):
                return
            filt = sql.get_filter(chat.id, keyword)
            if filt.reply == "yeni bir yan??t olmal??":
                buttons = sql.get_buttons(chat.id, filt.keyword)
                keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                VALID_WELCOME_FORMATTERS = [
                    "first",
                    "last",
                    "fullname",
                    "username",
                    "id",
                    "chatname",
                    "mention",
                ]
                if filt.reply_text:
                    if '%%%' in filt.reply_text:
                        split = filt.reply_text.split('%%%')
                        if all(split):
                            text = random.choice(split)
                        else:
                            text = filt.reply_text
                    else:
                        text = filt.reply_text
                    if text.startswith('~!') and text.endswith('!~'):
                        sticker_id = text.replace('~!', '').replace('!~', '')
                        try:
                            context.bot.send_sticker(
                                chat.id,
                                sticker_id,
                                reply_to_message_id=message.message_id)
                            return
                        except BadRequest as excp:
                            if excp.message == 'Yanl???? uzak dosya tan??mlay??c??s?? belirtildi: dizede yanl???? doldurma':
                                context.bot.send_message(
                                    chat.id,
                                    "Mesaj g??nderilemedi, ????kartma kimli??i ge??erli mi?"
                                )
                                return
                            else:
                                LOGGER.exception("Error in filters: " +
                                                 excp.message)
                                return
                    valid_format = escape_invalid_curly_brackets(
                        text, VALID_WELCOME_FORMATTERS)
                    if valid_format:
                        filtext = valid_format.format(
                            first=escape(message.from_user.first_name),
                            last=escape(message.from_user.last_name or
                                        message.from_user.first_name),
                            fullname=" ".join(
                                [
                                    escape(message.from_user.first_name),
                                    escape(message.from_user.last_name),
                                ] if message.from_user.last_name else
                                [escape(message.from_user.first_name)]),
                            username="@" + escape(message.from_user.username)
                            if message.from_user.username else mention_html(
                                message.from_user.id,
                                message.from_user.first_name),
                            mention=mention_html(message.from_user.id,
                                                 message.from_user.first_name),
                            chatname=escape(message.chat.title)
                            if message.chat.type != "private" else escape(
                                message.from_user.first_name),
                            id=message.from_user.id,
                        )
                    else:
                        filtext = ""
                else:
                    filtext = ""

                if filt.file_type in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    try:
                        context.bot.send_message(
                            chat.id,
                            markdown_to_html(filtext),
                            reply_to_message_id=message.message_id,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                        )
                    except BadRequest as excp:
                        error_catch = get_exception(excp, filt, chat)
                        if error_catch == "noreply":
                            try:
                                context.bot.send_message(
                                    chat.id,
                                    markdown_to_html(filtext),
                                    parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True,
                                    reply_markup=keyboard,
                                )
                            except BadRequest as excp:
                                LOGGER.exception("Error in filters: " +
                                                 excp.message)
                                send_message(
                                    update.effective_message,
                                    get_exception(excp, filt, chat),
                                )
                        else:
                            try:
                                send_message(
                                    update.effective_message,
                                    get_exception(excp, filt, chat),
                                )
                            except BadRequest as excp:
                                LOGGER.exception("Mesaj g??nderilemedi: " +
                                                 excp.message)
                                pass
                else:
                    try:
                        ENUM_FUNC_MAP[filt.file_type](
                            chat.id,
                            filt.file_id,
                            caption=markdown_to_html(filtext),
                            reply_to_message_id=message.message_id,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                        )
                    except BadRequest:
                        send_message(
                            message,
                            "Filtrenin i??eri??ini g??nderme iznim yok."
                        )
                break
            else:
                if filt.is_sticker:
                    message.reply_sticker(filt.reply)
                elif filt.is_document:
                    message.reply_document(filt.reply)
                elif filt.is_image:
                    message.reply_photo(filt.reply)
                elif filt.is_audio:
                    message.reply_audio(filt.reply)
                elif filt.is_voice:
                    message.reply_voice(filt.reply)
                elif filt.is_video:
                    message.reply_video(filt.reply)
                elif filt.has_markdown:
                    buttons = sql.get_buttons(chat.id, filt.keyword)
                    keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                    keyboard = InlineKeyboardMarkup(keyb)

                    try:
                        send_message(
                            update.effective_message,
                            filt.reply,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                        )
                    except BadRequest as excp:
                        if excp.message == "Unsupported url protocol":
                            try:
                                send_message(
                                    update.effective_message,
                                    "Desteklenmeyen bir url protokol?? kullanmaya ??al??????yorsunuz. "
                                    "Telegram, tg://. gibi baz?? protokoller i??in d????meleri desteklemez. L??tfen deneyin "
                                    "again...",
                                )
                            except BadRequest as excp:
                                LOGGER.exception("Error in filters: " +
                                                 excp.message)
                                pass
                        elif excp.message == "Cevap mesaj?? bulunamad??":
                            try:
                                context.bot.send_message(
                                    chat.id,
                                    filt.reply,
                                    parse_mode=ParseMode.MARKDOWN,
                                    disable_web_page_preview=True,
                                    reply_markup=keyboard,
                                )
                            except BadRequest as excp:
                                LOGGER.exception("Error in filters: " +
                                                 excp.message)
                                pass
                        else:
                            try:
                                send_message(
                                    update.effective_message,
                                    "Bu mesaj yanl???? bi??imlendirildi??i i??in g??nderilemedi.",
                                )
                            except BadRequest as excp:
                                LOGGER.exception("Error in filters: " +
                                                 excp.message)
                                pass
                            LOGGER.warning("Mesaj %s ayr????t??r??lamad??",
                                           str(filt.reply))
                            LOGGER.exception(
                                "%s sohbette %s filtresi ayr????t??r??lamad??",
                                str(filt.keyword),
                                str(chat.id),
                            )

                else:
                    # LEGACY - all new filters will have has_markdown set to True.
                    try:
                        send_message(update.effective_message, filt.reply)
                    except BadRequest as excp:
                        LOGGER.exception("Error in filters: " + excp.message)
                        pass
                break


@run_async
def rmall_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in DRAGONS:
        update.effective_message.reply_text(
            "Yaln??zca sohbet sahibi t??m notlar?? ayn?? anda temizleyebilir.")
    else:
        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="T??m filtreleri durdur", callback_data="filters_rmall")
        ], [
            InlineKeyboardButton(text="Cancel", callback_data="filters_cancel")
        ]])
        update.effective_message.reply_text(
            f"{chat.title} i??indeki T??M filtreleri durdurmak istedi??inizden emin misiniz ? Bu eylem geri al??namaz.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN)


@run_async
def rmall_callback(update, context):
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    member = chat.get_member(query.from_user.id)
    if query.data == 'filters_rmall':
        if member.status == "creator" or query.from_user.id in DRAGONS:
            allfilters = sql.get_chat_triggers(chat.id)
            if not allfilters:
                msg.edit_text("Bu sohbette filtre yok, durdurulacak bir ??ey yok!")
                return

            count = 0
            filterlist = []
            for x in allfilters:
                count += 1
                filterlist.append(x)

            for i in filterlist:
                sql.remove_filter(chat.id, i)

            msg.edit_text(f"temizlenmi??tir {count} filtrelerin {chat.title}")

        if member.status == "administrator":
            query.answer("Bunu yaln??zca sohbetin sahibi yapabilir.")

        if member.status == "member":
            query.answer("Bunu yapmak i??in y??netici olman??z gerekir.")
    elif query.data == 'filters_cancel':
        if member.status == "creator" or query.from_user.id in DRAGONS:
            msg.edit_text("T??m filtrelerin temizlenmesi iptal edildi.")
            return
        if member.status == "administrator":
            query.answer("Bunu yaln??zca sohbetin sahibi yapabilir.")
        if member.status == "member":
            query.answer("Bunu yapmak i??in y??netici olman??z gerekir.")


# NOT ASYNC NOT A HANDLER
def get_exception(excp, filt, chat):
    if excp.message == "Desteklenmeyen url protokol??":
        return "Desteklenmeyen URL protokol??n?? kullanmaya ??al??????yorsunuz. Telegram, tg: //. gibi birden ??ok protokol i??in anahtar?? desteklemiyor. L??tfen tekrar deneyin!"
    elif excp.message == "Cevap mesaj?? bulunamad??":
        return "noreply"
    else:
        LOGGER.warning("Mesaj %s ayr????t??r??lamad??", str(filt.reply))
        LOGGER.exception("%s sohbette %s filtrelenemedi",
                         str(filt.keyword), str(chat.id))
        return "Bu veriler yanl???? bi??imlendirildi??i i??in g??nderilemedi."


# NOT ASYNC NOT A HANDLER
def addnew_filter(update, chat_id, keyword, text, file_type, file_id, buttons):
    msg = update.effective_message
    totalfilt = sql.get_chat_triggers(chat_id)
    if len(totalfilt) >= 150:  # Idk why i made this like function....
        msg.reply_text("Bu grup, 150'lik maksimum filtre s??n??r??na ula??t??.")
        return False
    else:
        sql.new_add_filter(chat_id, keyword, text, file_type, file_id, buttons)
        return True


def __stats__():
    return "??? {} sohbetler aras??nda {} filtreleri.".format(sql.num_filters(),
                                                   sql.num_chats())


def __import_data__(chat_id, data):
    # set chat filters
    filters = data.get("filters", {})
    for trigger in filters:
        sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    cust_filters = sql.get_chat_triggers(chat_id)
    return "Burada `{}` ??zel filtre var.".format(len(cust_filters))


__help__ = """
 ??? `/filters`*:* Sohbette kay??tl?? t??m aktif filtreleri listeleyin.

*Yaln??zca y??netici:*
 ??? `/filter <keyword> <reply message>`*:* Bu sohbete bir filtre ekleyin. Bot art??k 'anahtar kelime' oldu??unda bu mesaj?? yan??tlayacakt??r\
bahsedilir. Bir ????kartmaya anahtar kelimeyle cevap verirseniz, bot bu ????kartma ile cevap verecektir. NOT: t??m filtre \
anahtar kelimeler k??????k harflidir. Anahtar kelimenizin bir c??mle olmas??n?? istiyorsan??z, t??rnak i??aretleri kullan??n. ??rne??in: /filter "hey orada" Nas??ls??n \
doin?
 Rastgele yan??tlar almak i??in fark yan??tlar??n?? `%%%` ile ay??r??n
 *??rnek:* 
 `/filter "dosya ad??"
 Cevap 1
 %%%
 Cevap 2
 %%%
 Cevap 3`
 ??? `/stop <filter keyword>`*:* Bu filtreyi durdurun.

*Yaln??zca sohbet olu??turucu:*
 ??? `/removeallfilters`*:* T??m sohbet filtrelerini bir defada kald??r??n.

*Not*: Filtreler ayr??ca: {first}, {last} etc .. ve d????meler gibi i??aretleme bi??imlendiricilerini de destekler.
Daha fazlas??n?? ????renmek i??in `/markdownhelp` i kontrol edin!

"""

__mod_name__ = "Filters"

FILTER_HANDLER = CommandHandler("filter", filters)
STOP_HANDLER = CommandHandler("stop", stop_filter)
RMALLFILTER_HANDLER = CommandHandler(
    "removeallfilters", rmall_filters, filters=Filters.group)
RMALLFILTER_CALLBACK = CallbackQueryHandler(
    rmall_callback, pattern=r"filters_.*")
LIST_HANDLER = DisableAbleCommandHandler(
    "filters", list_handlers, admin_ok=True)
CUST_FILTER_HANDLER = MessageHandler(
    CustomFilters.has_text & ~Filters.update.edited_message, reply_filter)

dispatcher.add_handler(FILTER_HANDLER)
dispatcher.add_handler(STOP_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(CUST_FILTER_HANDLER, HANDLER_GROUP)
dispatcher.add_handler(RMALLFILTER_HANDLER)
dispatcher.add_handler(RMALLFILTER_CALLBACK)

__handlers__ = [
    FILTER_HANDLER, STOP_HANDLER, LIST_HANDLER,
    (CUST_FILTER_HANDLER, HANDLER_GROUP, RMALLFILTER_HANDLER)
]
