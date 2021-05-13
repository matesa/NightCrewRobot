import time
import re

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, Update, Bot
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, CallbackQueryHandler, run_async

import SaitamaRobot.modules.sql.connection_sql as sql
from SaitamaRobot import dispatcher, DRAGONS, DEV_USERS
from SaitamaRobot.modules.helper_funcs import chat_status
from SaitamaRobot.modules.helper_funcs.alternate import send_message, typing_action

user_admin = chat_status.user_admin


@user_admin
@run_async
@typing_action
def allow_connections(update, context) -> str:

    chat = update.effective_chat
    args = context.args

    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if var == "no":
                sql.set_allow_connect_to_chat(chat.id, False)
                send_message(
                    update.effective_message,
                    "Bu sohbet için bağlantı devre dışı bırakıldı",
                )
            elif var == "yes":
                sql.set_allow_connect_to_chat(chat.id, True)
                send_message(
                    update.effective_message,
                    "Bu sohbet için bağlantı etkinleştirildi",
                )
            else:
                send_message(
                    update.effective_message,
                    "Lütfen `yes` or `no` girin!",
                    parse_mode=ParseMode.MARKDOWN,
                )
        else:
            get_settings = sql.allow_connect_to_chat(chat.id)
            if get_settings:
                send_message(
                    update.effective_message,
                    "Bu gruba bağlantılar üyeler için *İzin verilir*!",
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                send_message(
                    update.effective_message,
                    "Bu gruba bağlantı üyeler için *İzin Verilmez*!",
                    parse_mode=ParseMode.MARKDOWN,
                )
    else:
        send_message(update.effective_message,
                     "Bu komut yalnızca grup içindir. Pm için değil!")


@run_async
@typing_action
def connection_chat(update, context):

    chat = update.effective_chat
    user = update.effective_user

    conn = connected(context.bot, update, chat, user.id, need_admin=True)

    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type != "private":
            return
        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    if conn:
        message = "Şu anda {} ile bağlısınız.\n".format(chat_name)
    else:
        message = "Şu anda herhangi bir gruba bağlı değilsiniz.\n"
    send_message(update.effective_message, message, parse_mode="markdown")


@run_async
@typing_action
def connect_chat(update, context):

    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if update.effective_chat.type == "private":
        if args and len(args) >= 1:
            try:
                connect_chat = int(args[0])
                getstatusadmin = context.bot.get_chat_member(
                    connect_chat, update.effective_message.from_user.id)
            except ValueError:
                try:
                    connect_chat = str(args[0])
                    get_chat = context.bot.getChat(connect_chat)
                    connect_chat = get_chat.id
                    getstatusadmin = context.bot.get_chat_member(
                        connect_chat, update.effective_message.from_user.id)
                except BadRequest:
                    send_message(update.effective_message, "Geçersiz Sohbet Kimliği!")
                    return
            except BadRequest:
                send_message(update.effective_message, "Geçersiz Sohbet Kimliği!")
                return

            isadmin = getstatusadmin.status in ("administrator", "creator")
            ismember = getstatusadmin.status in ("member")
            isallow = sql.allow_connect_to_chat(connect_chat)

            if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
                connection_status = sql.connect(
                    update.effective_message.from_user.id, connect_chat)
                if connection_status:
                    conn_chat = dispatcher.bot.getChat(
                        connected(
                            context.bot,
                            update,
                            chat,
                            user.id,
                            need_admin=False))
                    chat_name = conn_chat.title
                    send_message(
                        update.effective_message,
                        "*{}* Öğesine başarıyla bağlandı. \nKullanılabilir komutları kontrol etmek için /helpconnect kullanın."
                        .format(chat_name),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
                else:
                    send_message(update.effective_message, "Bağlantı kurulamadı!")
            else:
                send_message(update.effective_message,
                             "Bu sohbete bağlantıya izin verilmiyor!")
        else:
            gethistory = sql.get_history_conn(user.id)
            if gethistory:
                buttons = [
                    InlineKeyboardButton(
                        text="❎ Kapat düğmesi", callback_data="connect_close"),
                    InlineKeyboardButton(
                        text="🧹 Geçmişi temizle", callback_data="connect_clear"),
                ]
            else:
                buttons = []
            conn = connected(
                context.bot, update, chat, user.id, need_admin=False)
            if conn:
                connectedchat = dispatcher.bot.getChat(conn)
                text = "Şu anda *{}* (`{}`) ile bağlısınız".format(
                    connectedchat.title, conn)
                buttons.append(
                    InlineKeyboardButton(
                        text="🔌 Bağlantıyı Kes",
                        callback_data="connect_disconnect"))
            else:
                text = "Bağlanmak için sohbet kimliğini veya etiketi yazın!"
            if gethistory:
                text += "\n\n*Bağlantı geçmişi:*\n"
                text += "╒═══「 *Bilgi* 」\n"
                text += "│  Sıralandı: `En Yeni`\n"
                text += "│\n"
                buttons = [buttons]
                for x in sorted(gethistory.keys(), reverse=True):
                    htime = time.strftime("%d/%m/%Y", time.localtime(x))
                    text += "╞═「 *{}* 」\n│   `{}`\n│   `{}`\n".format(
                        gethistory[x]["chat_name"], gethistory[x]["chat_id"],
                        htime)
                    text += "│\n"
                    buttons.append([
                        InlineKeyboardButton(
                            text=gethistory[x]["chat_name"],
                            callback_data="connect({})".format(
                                gethistory[x]["chat_id"]),
                        )
                    ])
                text += "╘══「 Toplam {} Sohbet 」".format(
                    str(len(gethistory)) +
                    " (max)" if len(gethistory) == 5 else str(len(gethistory)))
                conn_hist = InlineKeyboardMarkup(buttons)
            elif buttons:
                conn_hist = InlineKeyboardMarkup([buttons])
            else:
                conn_hist = None
            send_message(
                update.effective_message,
                text,
                parse_mode="markdown",
                reply_markup=conn_hist,
            )

    else:
        getstatusadmin = context.bot.get_chat_member(
            chat.id, update.effective_message.from_user.id)
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(chat.id)
        if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
            connection_status = sql.connect(
                update.effective_message.from_user.id, chat.id)
            if connection_status:
                chat_name = dispatcher.bot.getChat(chat.id).title
                send_message(
                    update.effective_message,
                    "*{}* İle başarıyla bağlandı.".format(chat_name),
                    parse_mode=ParseMode.MARKDOWN,
                )
                try:
                    sql.add_history_conn(user.id, str(chat.id), chat_name)
                    context.bot.send_message(
                        update.effective_message.from_user.id,
                        "*{}* 'A bağlısınız. \nKullanılabilir komutları kontrol etmek için `/helpconnect` kullanın."
                        .format(chat_name),
                        parse_mode="markdown",
                    )
                except BadRequest:
                    pass
                except Unauthorized:
                    pass
            else:
                send_message(update.effective_message, "Bağlantı kurulamadı!")
        else:
            send_message(update.effective_message,
                         "Bu sohbete bağlantıya izin verilmiyor!")


def disconnect_chat(update, context):

    if update.effective_chat.type == "private":
        disconnection_status = sql.disconnect(
            update.effective_message.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = send_message(update.effective_message,
                                                 "Sohbet bağlantısı kesildi!")
        else:
            send_message(update.effective_message, "Sen bağlı değil demektir!")
    else:
        send_message(update.effective_message,
                     "Bu komut yalnızca PM'de mevcuttur.")


def connected(bot: Bot, update: Update, chat, user_id, need_admin=True):
    user = update.effective_user

    if chat.type == chat.PRIVATE and sql.get_connected_chat(user_id):

        conn_id = sql.get_connected_chat(user_id).chat_id
        getstatusadmin = bot.get_chat_member(
            conn_id, update.effective_message.from_user.id)
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(conn_id)

        if ((isadmin) or (isallow and ismember) or (user.id in DRAGONS) or
            (user.id in DEV_USERS)):
            if need_admin is True:
                if (getstatusadmin.status in ("administrator", "creator") or
                        user_id in DRAGONS or user.id in DEV_USERS):
                    return conn_id
                else:
                    send_message(
                        update.effective_message,
                        "Bağlı grupta yönetici olmalısınız!",
                    )
            else:
                return conn_id
        else:
            send_message(
                update.effective_message,
                "Grup bağlantı haklarını değiştirdi veya artık yönetici değilsiniz.\nBağlantınızı kestim.",
            )
            disconnect_chat(update, bot)
    else:
        return False


CONN_HELP = """
 Eylemler bağlı gruplarla kullanılabilir:
 • Notları görüntüleyin ve düzenleyin.
 • Filtreleri görüntüleyin ve düzenleyin.
 • Sohbetin davet bağlantısını alın.
 • AntiFlood ayarlarını yapın ve kontrol edin.
 • Kara Liste ayarlarını belirleyin ve kontrol edin.
 • Sohbette Kilitleri ve Kilidi Açmaları ayarlayın.
 • Sohbette komutları etkinleştirin ve devre dışı bırakın.
 • Sohbet yedeklemesinin Dışa Aktarımı ve İçe Aktarımı.
 • Gelecekte daha fazlası!"""


@run_async
def help_connect_chat(update, context):

    args = context.args

    if update.effective_message.chat.type != "private":
        send_message(update.effective_message,
                     "Yardım almak için bana bu komutla PM atın.")
        return
    else:
        send_message(update.effective_message, CONN_HELP, parse_mode="markdown")


@run_async
def connect_button(update, context):

    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user

    connect_match = re.match(r"connect\((.+?)\)", query.data)
    disconnect_match = query.data == "connect_disconnect"
    clear_match = query.data == "connect_clear"
    connect_close = query.data == "connect_close"

    if connect_match:
        target_chat = connect_match.group(1)
        getstatusadmin = context.bot.get_chat_member(target_chat,
                                                     query.from_user.id)
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(target_chat)

        if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
            connection_status = sql.connect(query.from_user.id, target_chat)

            if connection_status:
                conn_chat = dispatcher.bot.getChat(
                    connected(
                        context.bot, update, chat, user.id, need_admin=False))
                chat_name = conn_chat.title
                query.message.edit_text(
                    "*{}* Öğesine başarıyla bağlandı. \nKullanılabilir komutları kontrol etmek için `/helpconnect` kullanın."
                    .format(chat_name),
                    parse_mode=ParseMode.MARKDOWN,
                )
                sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
            else:
                query.message.edit_text("Bağlantı başarısız!")
        else:
            context.bot.answer_callback_query(
                query.id,
                "Bu sohbete bağlantıya izin verilmiyor!",
                show_alert=True)
    elif disconnect_match:
        disconnection_status = sql.disconnect(query.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = query.message.edit_text(
                "Sohbet bağlantısı kesildi!")
        else:
            context.bot.answer_callback_query(
                query.id, "Bağlı değilsiniz!", show_alert=True)
    elif clear_match:
        sql.clear_history_conn(query.from_user.id)
        query.message.edit_text("Bağlanan geçmiş temizlendi!")
    elif connect_close:
        query.message.edit_text("Kapalı.\nTekrar açmak için yazın /connect")
    else:
        connect_chat(update, context)


__mod_name__ = "Connection"

__help__ = """
Bazen, bir grup sohbetine bazı notlar ve filtreler eklemek istersiniz, ancak herkesin görmesini istemezsiniz; Bağlantıların devreye girdiği yer burasıdır...
Bu, bir sohbetin veritabanına bağlanmanıza ve sohbette görünen komutlar olmadan ona bir şeyler eklemenize olanak tanır! Bariz nedenlerden dolayı, bir şeyler eklemek için yönetici olmanız gerekir; ancak gruptaki herhangi bir üye verilerinizi görüntüleyebilir.

 • /connect: Sohbete bağlanır (Bir grupta /connect veya /connect <sohbet id> sonra yapılabilir)
 • /connection: Bağlı sohbetleri listele
 • /disconnect: Sohbet bağlantısını kesin
 • /helpconnect: Uzaktan kullanılabilecek mevcut komutları listeleyin

*Yalnızca yönetici:*
 • /allowconnect <yes/no>: kullanıcının sohbete bağlanmasına izin ver
"""

CONNECT_CHAT_HANDLER = CommandHandler("connect", connect_chat, pass_args=True)
CONNECTION_CHAT_HANDLER = CommandHandler("connection", connection_chat)
DISCONNECT_CHAT_HANDLER = CommandHandler("disconnect", disconnect_chat)
ALLOW_CONNECTIONS_HANDLER = CommandHandler(
    "allowconnect", allow_connections, pass_args=True)
HELP_CONNECT_CHAT_HANDLER = CommandHandler("helpconnect", help_connect_chat)
CONNECT_BTN_HANDLER = CallbackQueryHandler(connect_button, pattern=r"connect")

dispatcher.add_handler(CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECTION_CHAT_HANDLER)
dispatcher.add_handler(DISCONNECT_CHAT_HANDLER)
dispatcher.add_handler(ALLOW_CONNECTIONS_HANDLER)
dispatcher.add_handler(HELP_CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECT_BTN_HANDLER)
