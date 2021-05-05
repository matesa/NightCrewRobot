import html
from typing import Optional

from SaitamaRobot import LOGGER, TIGERS, dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import (bot_admin,
                                                           can_restrict,
                                                           connection_status,
                                                           is_user_admin,
                                                           user_admin)
from SaitamaRobot.modules.helper_funcs.extraction import (extract_user,
                                                          extract_user_and_text)
from SaitamaRobot.modules.helper_funcs.string_handling import extract_time
from SaitamaRobot.modules.log_channel import loggable
from telegram import Bot, Chat, ChatPermissions, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html


def check_user(user_id: int, bot: Bot, chat: Chat) -> Optional[str]:
    if not user_id:
        reply = "Bir kullanıcıya atıfta bulunmuyorsunuz veya belirtilen kimlik yanlış.."
        return reply

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            reply = "Bu kullanıcıyı bulamıyorum"
            return reply
        else:
            raise

    if user_id == bot.id:
        reply = "Ben de MUTE etmeyeceğim, Ne kadar yüksektesin?"
        return reply

    if is_user_admin(chat, user_id, member) or user_id in TIGERS:
        reply = "Yapamam. Sesini kapatmak için başka birini bulun ama bunu değil."
        return reply

    return None


@run_async
@connection_status
@bot_admin
@user_admin
@loggable
def mute(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#MUTE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}")

    if reason:
        log += f"\n<b>Neden:</b> {reason}"

    if member.can_send_messages is None or member.can_send_messages:
        chat_permissions = ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(chat.id, user_id, chat_permissions)
        bot.sendMessage(
            chat.id,
            f"Son kullanma tarihi olmaksızın <b>{html.escape(member.user.first_name)}</b> kapatıldı!",
            parse_mode=ParseMode.HTML)
        return log

    else:
        message.reply_text("Bu kullanıcının sesi zaten kapatılmış!")

    return ""


@run_async
@connection_status
@bot_admin
@user_admin
@loggable
def unmute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "Ya sesi açmak için bana bir kullanıcı adı vermeniz ya da sesi açılacak birine yanıt vermeniz gerekecek."
        )
        return ""

    member = chat.get_member(int(user_id))

    if member.status != 'kicked' and member.status != 'left':
        if (member.can_send_messages and member.can_send_media_messages and
                member.can_send_other_messages and
                member.can_add_web_page_previews):
            message.reply_text("Bu kullanıcının zaten konuşma hakkı var.")
        else:
            chat_permissions = ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True)
            try:
                bot.restrict_chat_member(chat.id, int(user_id),
                                         chat_permissions)
            except BadRequest:
                pass
            bot.sendMessage(
                chat.id,
                f"<b>{html.escape(member.user.first_name)}</b> 'nın metin yazmasına izin vermeliyim!",
                parse_mode=ParseMode.HTML)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNMUTE\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
            )
    else:
        message.reply_text(
            "Bu kullanıcı sohbette bile değil, sesini açmak, onlardan daha fazla konuşmasını sağlamaz "
            "zaten yap!")

    return ""


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    if not reason:
        message.reply_text(
            "Bu kullanıcının sesini kapatmak için bir zaman belirtmediniz!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#TEMP MUTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Time:</b> {time_val}")
    if reason:
        log += f"\n<b>Neden:</b> {reason}"

    try:
        if member.can_send_messages is None or member.can_send_messages:
            chat_permissions = ChatPermissions(can_send_messages=False)
            bot.restrict_chat_member(
                chat.id, user_id, chat_permissions, until_date=mutetime)
            bot.sendMessage(
                chat.id,
                f"<b>{html.escape(member.user.first_name)}</b> for {time_val} yoksayıldı!",
                parse_mode=ParseMode.HTML)
            return log
        else:
            message.reply_text("Bu kullanıcının sesi zaten kapatılmış.")

    except BadRequest as excp:
        if excp.message == "Cevap mesajı bulunamadı":
            # Do not reply
            message.reply_text(f"{time_val} yoksayıldı!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(" %s sohbetinde %s (%s) kullanıcısını %s nedeniyle sessize alma HATASI",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Lanet olsun, bu kullanıcının sesini kapatamıyorum.")

    return ""


__help__ = """
*Yalnızca yöneticiler:*
 • `/mute <userhandle>`*:* kullanıcıyı susturur. Ayrıca, yanıtlanan kullanıcının sesini kapatarak bir yanıt olarak da kullanılabilir.
 • `/tmute <userhandle> x(m/h/d)`*:* kullanıcıyı x kez susturur. (tanıtıcı veya yanıt yoluyla). `m` = `Dakika`, `h` = `Saat`, `d` = `Gün`.
 • `/unmute <userhandle>`*:* bir kullanıcının sesini açar. Ayrıca, yanıtlanan kullanıcının sesini kapatarak bir yanıt olarak da kullanılabilir.
"""

MUTE_HANDLER = CommandHandler("mute", mute)
UNMUTE_HANDLER = CommandHandler("unmute", unmute)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"], temp_mute)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)

__mod_name__ = "Muting"
__handlers__ = [MUTE_HANDLER, UNMUTE_HANDLER, TEMPMUTE_HANDLER]
