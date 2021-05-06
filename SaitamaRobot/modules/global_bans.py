import html
import time
from datetime import datetime
from io import BytesIO

from telegram import ParseMode, Update
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, run_async)
from telegram.utils.helpers import mention_html

import SaitamaRobot.modules.sql.global_bans_sql as sql
from SaitamaRobot.modules.sql.users_sql import get_user_com_chats
from SaitamaRobot import (DEV_USERS, EVENT_LOGS, OWNER_ID, STRICT_GBAN, DRAGONS,
                          SUPPORT_CHAT, SPAMWATCH_SUPPORT_CHAT, DEMONS, TIGERS,
                          WOLVES, sw, dispatcher)
from SaitamaRobot.modules.helper_funcs.chat_status import (is_user_admin,
                                                           support_plus,
                                                           user_admin)
from SaitamaRobot.modules.helper_funcs.extraction import (extract_user,
                                                          extract_user_and_text)
from SaitamaRobot.modules.helper_funcs.misc import send_to_list

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "Kullanıcı, sohbetin yöneticisidir",
    "Sohbet bulunamadı",
    "Sohbet üyesini kısıtlamak/unrestrict yeterli hak yok",
    "User_not_participant",
    "Peer_id_invalid",
    "Grup sohbeti devre dışı bırakıldı",
    "Bir kullanıcıyı temel bir gruptan atması için davetkar olması gerekir",
    "Chat_admin_required",
    "Yalnızca temel bir grubu oluşturan kişi grup yöneticilerini atabilir",
    "Channel_private",
    "Sohbette değil",
    "Sohbet sahibi kaldırılamıyor",
}

UNGBAN_ERRORS = {
    "Kullanıcı, sohbetin yöneticisidir",
    "Sohbet bulunamadı",
    "Sohbet üyesini kısıtlamak/unrestrict için yeterli hak yok",
    "User_not_participant",
    "Yöntem yalnızca üst grup ve kanal sohbetleri için kullanılabilir",
    "Sohbette değil",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
    "Kullanıcı bulunamadı",
}


@run_async
@support_plus
def gban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Bir kullanıcıya atıfta bulunmuyorsunuz veya belirtilen kimlik yanlış.."
        )
        return

    if int(user_id) in DEV_USERS:
        message.reply_text(
            "Bu kullanıcı Derneğin bir parçası\nKendi aleyhimize hareket edemem."
        )
        return

    if int(user_id) in DRAGONS:
        message.reply_text(
            "Küçük gözümle casusluk yapıyorum ... bir felaket! Neden birbirinize düşman oluyorsunuz?"
        )
        return

    if int(user_id) in DEMONS:
        message.reply_text(
            "OOOH birisi bir Demon Felaketini yakalamaya çalışıyor! *Patlamış mısır kapıyor*")
        return

    if int(user_id) in TIGERS:
        message.reply_text("Bu bir Kaplan! Yasaklanamazlar!")
        return

    if int(user_id) in WOLVES:
        message.reply_text("Bu bir Kurt! Yasaklanamazlar!")
        return

    if user_id == bot.id:
        message.reply_text("Ahh ... kendime yumruk atmamı mı istiyorsun?")
        return

    if user_id in [777000, 1087968824]:
        message.reply_text("Aptal! Telegram'ın yerel teknolojisine saldıramazsınız!")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            message.reply_text("Bu kullanıcıyı bulamıyorum.")
            return ""
        else:
            return

    if user_chat.type != 'private':
        message.reply_text("Bu bir kullanıcı değil!")
        return

    if sql.is_user_gbanned(user_id):

        if not reason:
            message.reply_text(
                "Bu kullanıcı zaten yasaklanmış; nedenini değiştirirdim, ancak bana bir tane vermediniz..."
            )
            return

        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            message.reply_text(
                "Bu kullanıcı, aşağıdaki nedenden dolayı zaten yasaklanmış durumda:\n"
                "<code>{}</code>\n"
                "Gittim ve yeni sebebinizle güncelledim!".format(
                    html.escape(old_reason)),
                parse_mode=ParseMode.HTML)

        else:
            message.reply_text(
                "Bu kullanıcı zaten yasaklanmış, ancak belirlenmemiş bir nedeni yok; gittim ve güncelledim!"
            )

        return

    message.reply_text("Üzerinde!")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != 'private':
        chat_origin = "<b>{} ({})</b>\n".format(
            html.escape(chat.title), chat.id)
    else:
        chat_origin = "<b>{}</b>\n".format(chat.id)

    log_message = (
        f"#GBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Banned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Banned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>")

    if reason:
        if chat.type == chat.SUPERGROUP and chat.username:
            log_message += f"\n<b>Reason:</b> <a href=\"https://telegram.me/{chat.username}/{message.message_id}\">{reason}</a>"
        else:
            log_message += f"\n<b>Reason:</b> <code>{reason}</code>"

    if EVENT_LOGS:
        try:
            log = bot.send_message(
                EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS, log_message +
                "\n\nBeklenmeyen bir hata nedeniyle biçimlendirme devre dışı bırakıldı.")

    else:
        send_to_list(bot, DRAGONS + DEMONS, log_message, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_user_com_chats(user_id)
    gbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text(f"gban Could dolayı: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"nedeniyle gban yapılamadı {excp.message}",
                        parse_mode=ParseMode.HTML)
                else:
                    send_to_list(bot, DRAGONS + DEMONS,
                                 f"nedeniyle gban yapılamadı: {excp.message}")
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if EVENT_LOGS:
        log.edit_text(
            log_message +
            f"\n<b>Etkilenen sohbetler:</b> <code>{gbanned_chats}</code>",
            parse_mode=ParseMode.HTML)
    else:
        send_to_list(
            bot,
            DRAGONS + DEMONS,
            f"Gban tamamlandı! <code>{gbanned_chats}</code> sohbetlerinde yasaklandı)",
            html=True)

    end_time = time.time()
    gban_time = round((end_time - start_time), 2)

    if gban_time > 60:
        gban_time = round((gban_time / 60), 2)
        message.reply_text("Bitti! Gbanned.", parse_mode=ParseMode.HTML)
    else:
        message.reply_text("Bitti! Gbanned.", parse_mode=ParseMode.HTML)

    try:
        bot.send_message(
            user_id, "#EVENT"
            "Kötü Amaçlı olarak işaretlendiniz ve bu nedenle yöneteceğimiz tüm gruplardan yasaklandınız."
            f"\n<b>neden:</b> <code>{html.escape(user.reason)}</code>"
            f"</b>Temyiz Sohbeti:</b> @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML)
    except:
        pass  # bot probably blocked by user


@run_async
@support_plus
def ungban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "Bir kullanıcıya atıfta bulunmuyorsunuz veya belirtilen kimlik yanlış.."
        )
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("Bu bir kullanıcı değil!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("Bu kullanıcı yasaklanmadı!")
        return

    message.reply_text(
        f" {user_chat.first_name} adlı kullanıcıya küresel olarak ikinci bir şans vereceğim.")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != 'private':
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#UNGBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Unbanned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Unbanned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>")

    if EVENT_LOGS:
        try:
            log = bot.send_message(
                EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS, log_message +
                "\n\nBeklenmeyen bir hata nedeniyle biçimlendirme devre dışı bırakıldı.")
    else:
        send_to_list(bot, DRAGONS + DEMONS, log_message, html=True)

    chats = get_user_com_chats(user_id)
    ungbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Acaba un-gban değil nedeniyle: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"nedeniyle gban kaldırılamadı: {excp.message}",
                        parse_mode=ParseMode.HTML)
                else:
                    bot.send_message(
                        OWNER_ID, f"nedeniyle gban kaldırılamadı: {excp.message}")
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if EVENT_LOGS:
        log.edit_text(
            log_message + f"\n<b>Etkilenen sohbetler:</b> {ungbanned_chats}",
            parse_mode=ParseMode.HTML)
    else:
        send_to_list(bot, DRAGONS + DEMONS, "un-gban tam!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        message.reply_text(
            f"Kişinin yasağı kaldırıldı {ungban_time} min")
    else:
        message.reply_text(
            f"Kişinin yasağı kaldırıldı {ungban_time} sec")


@run_async
@support_plus
def gbanlist(update: Update, context: CallbackContext):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "Yasaklı kullanıcı yok! Beklediğimden daha naziksiniz...")
        return

    banfile = 'Bu adamları boşverin.\n'
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["reason"]:
            banfile += f"Reason: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="İşte şu anda yasaklanmış kullanıcıların listesi.")


def check_and_ban(update, user_id, should_message=True):

    chat = update.effective_chat  # type: Optional[Chat]
    try:
        sw_ban = sw.get_ban(int(user_id))
    except:
        sw_ban = None

    if sw_ban:
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text(
                f"<b>Alert</b>: bu kullanıcı global olarak yasaklanmıştır.\n"
                f"<code>*onları buradan yasaklar*</code>.\n"
                f"<b>Sohbete itiraz edin</b>: {SPAMWATCH_SUPPORT_CHAT}\n"
                f"<b>User ID</b>: <code>{sw_ban.id}</code>\n"
                f"<b>Ban Reason</b>: <code>{html.escape(sw_ban.reason)}</code>",
                parse_mode=ParseMode.HTML)
        return

    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            text = f"<b>Alert</b>: this user is globally banned.\n" \
                   f"<code>*bans them from here*</code>.\n" \
                   f"<b>Appeal chat</b>: @{SUPPORT_CHAT}\n" \
                   f"<b>User ID</b>: <code>{user_id}</code>"
            user = sql.get_gbanned_user(user_id)
            if user.reason:
                text += f"\n<b>Ban Reason:</b> <code>{html.escape(user.reason)}</code>"
            update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def enforce_gban(update: Update, context: CallbackContext):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    bot = context.bot
    try:
        restrict_permission = update.effective_chat.get_member(
            bot.id).can_restrict_members
    except Unauthorized:
        return
    if sql.does_chat_gban(update.effective_chat.id) and restrict_permission:
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "Antispam artık etkindir ✅ "
                "Artık grubunuzu olası uzak tehditlerden koruyorum!")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("Antispan artık devre dışıdır ❌ "
                                                "Spamwatch artık devre dışı bırakıldı ❌")
    else:
        update.effective_message.reply_text(
            "Bir ayar seçmek için bana bazı argümanlar verin! on/off, yes/no!\n\n"
            "Mevcut ayarınız: {}\n"
            "True olduğunda, gerçekleşen herhangi bir gbans grubunuzda da olacaktır. "
            "Yanlış olduğunda, sizi olası merhametine bırakarak yapmazlar "
            "spam gönderenler.".format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return f"• {sql.num_gbanned_users()} gbanned users."


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)
    text = "Kötü Amaçlı: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in DRAGONS + TIGERS + WOLVES:
        return ""
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += f"\n<b>Neden:</b> <code>{html.escape(user.reason)}</code>"
        text += f"\n<b>Temyiz Sohbeti:</b> @{SUPPORT_CHAT}"
    else:
        text = text.format("???")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"Bu sohbet *gbans* uyguluyor: `{sql.does_chat_gban(chat_id)}`."


__help__ = f"""
*Yalnızca yöneticiler:*
 • `/antispam <on/off/yes/no>`*:* Antispam teknolojimizi değiştirecek veya mevcut ayarlarınızı döndürecektir.

Anti-Spam, bot geliştiricileri tarafından spam gönderenleri tüm gruplarda yasaklamak için kullanılır. Bu korumaya yardımcı olur \
spam sel baskınlarını olabildiğince çabuk kaldırarak siz ve gruplarınız.
*Not:* Kullanıcılar, @{SUPPORT_CHAT} adresinden gban'lara itiraz edebilir veya spam yapanları bildirebilir

Bu ayrıca Spam gönderenleri sohbet odanızdan olabildiğince kaldırmak için Spamwatch API'sini de entegre eder!
*SpamWatch nedir?*
SpamWatch spambotlar, troller, bitcoin spam göndericileri ve tatsız karakterlerinsürekli güncellenen büyük bir yasak listesini tutar)
İstenmeyen posta gönderenlerin grubunuzdan otomatik olarak uzaklaştırılmasına sürekli yardım edin Bu nedenle, spam gönderenlerin grubunuza saldırması konusunda endişelenmenize gerek kalmaz.
*Not:* Kullanıcılar spamwatch yasaklarına @Poyraz2103 adresinden itiraz edebilir
"""

GBAN_HANDLER = CommandHandler("gban", gban)
UNGBAN_HANDLER = CommandHandler("ungban", ungban)
GBAN_LIST = CommandHandler("gbanlist", gbanlist)

GBAN_STATUS = CommandHandler("antispam", gbanstat, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

__mod_name__ = "Anti-Spam"
__handlers__ = [GBAN_HANDLER, UNGBAN_HANDLER, GBAN_LIST, GBAN_STATUS]

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
    __handlers__.append((GBAN_ENFORCER, GBAN_ENFORCE_GROUP))
