from datetime import datetime
from functools import wraps

from telegram.ext import CallbackContext

from SaitamaRobot.modules.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import ParseMode, Update
    from telegram.error import BadRequest, Unauthorized
    from telegram.ext import CommandHandler, JobQueue, run_async
    from telegram.utils.helpers import escape_markdown

    from SaitamaRobot import EVENT_LOGS, LOGGER, dispatcher
    from SaitamaRobot.modules.helper_funcs.chat_status import user_admin
    from SaitamaRobot.modules.sql import log_channel_sql as sql

    def loggable(func):

        @wraps(func)
        def log_action(update: Update,
                       context: CallbackContext,
                       job_queue: JobQueue = None,
                       *args,
                       **kwargs):
            if not job_queue:
                result = func(update, context, *args, **kwargs)
            else:
                result = func(update, context, job_queue, *args, **kwargs)

            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += f"\n<b>Olay Damgası</b>: <code>{datetime.utcnow().strftime(datetime_fmt)}</code>"

                if message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
                log_chat = sql.get_chat_log_channel(chat.id)
                if log_chat:
                    send_log(context, log_chat, chat.id, result)

            return result

        return log_action

    def gloggable(func):

        @wraps(func)
        def glog_action(update: Update, context: CallbackContext, *args,
                        **kwargs):
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += "\n<b>Olay Damgası</b>: <code>{}</code>".format(
                    datetime.utcnow().strftime(datetime_fmt))

                if message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
                log_chat = str(EVENT_LOGS)
                if log_chat:
                    send_log(context, log_chat, chat.id, result)

            return result

        return glog_action

    def send_log(context: CallbackContext, log_chat_id: str, orig_chat_id: str,
                 result: str):
        bot = context.bot
        try:
            bot.send_message(
                log_chat_id,
                result,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True)
        except BadRequest as excp:
            if excp.message == "Sohbet bulunamadı":
                bot.send_message(
                    orig_chat_id,
                    "Bu günlük kanalı silindi - ayarlanmıyor.")
                sql.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("ayrıştırılamadı")

                bot.send_message(
                    log_chat_id, result +
                    "\n\nBeklenmeyen bir hata nedeniyle biçimlendirme devre dışı bırakıldı."
                )

    @run_async
    @user_admin
    def logging(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.get_chat_log_channel(chat.id)
        if log_channel:
            log_channel_info = bot.get_chat(log_channel)
            message.reply_text(
                f"Bu grubun tüm günlükleri şuraya gönderilmiştir:"
                f" {escape_markdown(log_channel_info.title)} (`{log_channel}`)",
                parse_mode=ParseMode.MARKDOWN)

        else:
            message.reply_text("Bu grup için günlük kanalı ayarlanmadı!")

    @run_async
    @user_admin
    def setlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat
        if chat.type == chat.CHANNEL:
            message.reply_text(
                "Şimdi, /setlog'u bu kanalı bağlamak istediğiniz gruba iletin!"
            )

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Silinecek mesaj bulunamadı":
                    pass
                else:
                    LOGGER.exception(
                        "Günlük kanalındaki mesaj silinirken hata oluştu. Yine de çalışmalı."
                    )

            try:
                bot.send_message(
                    message.forward_from_chat.id,
                    f"Bu kanal, {chat.title or chat.first_name} için günlük kanalı olarak ayarlandı."
                )
            except Unauthorized as excp:
                if excp.message == "Yasak: bot, kanal sohbetinin bir üyesi değil":
                    bot.send_message(chat.id, "Başarıyla log kanal ayarlandı!")
                else:
                    LOGGER.exception("Günlük kanalını ayarlarken HATA.")

            bot.send_message(chat.id, "Başarıyla log kanal ayarlandı!")

        else:
            message.reply_text("Bir günlük kanalı belirleme adımları şunlardır:\n"
                               " - botu istenen kanala ekleyin\n"
                               " - kanala /setlog komutunu gönderin\n"
                               " - /setlog'u gruba iletin\n")

    @run_async
    @user_admin
    def unsetlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            bot.send_message(log_channel,
                             f"Kanalın {chat.title} ile bağlantısı kaldırıldı")
            message.reply_text("Günlük kanalı ayarlanmamış.")

        else:
            message.reply_text("Henüz bir günlük kanalı ayarlanmadı!")

    def __stats__():
        return f"• {sql.num_logchannels()} günlük kanalları ayarlandı."

    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return f"Bu grubun tüm günlükleri şu adrese gönderildi: {escape_markdown(log_channel_info.title)} (`{log_channel}`)"
        return "Bu grup için günlük kanalı ayarlanmadı!"

    __help__ = """
*Yalnızca yöneticiler:*
• `/logchannel`*:* günlük kanalı bilgilerini al
• `/setlog`*:* günlük kanalını ayarlayın.
• `/unsetlog`*:* günlük kanalının ayarını kaldırır.

Günlük kanalının ayarlanması şu şekilde yapılır:
• botu istenen kanala eklemek (yönetici olarak!)
• kanalda `/setlog` gönderme
• `/setlog` 'u gruba iletmek
"""

    __mod_name__ = "Log Channels"

    LOG_HANDLER = CommandHandler("logchannel", logging)
    SET_LOG_HANDLER = CommandHandler("setlog", setlog)
    UNSET_LOG_HANDLER = CommandHandler("unsetlog", unsetlog)

    dispatcher.add_handler(LOG_HANDLER)
    dispatcher.add_handler(SET_LOG_HANDLER)
    dispatcher.add_handler(UNSET_LOG_HANDLER)

else:
    # run anyway if module not loaded
    def loggable(func):
        return func

    def gloggable(func):
        return func
