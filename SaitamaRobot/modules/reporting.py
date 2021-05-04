import html

from SaitamaRobot import (LOGGER, DRAGONS, TIGERS, WOLVES, dispatcher)
from SaitamaRobot.modules.helper_funcs.chat_status import (user_admin,
                                                           user_not_admin)
from SaitamaRobot.modules.log_channel import loggable
from SaitamaRobot.modules.sql import reporting_sql as sql
from telegram import (Chat, InlineKeyboardButton, InlineKeyboardMarkup,
                      ParseMode, Update)
from telegram.error import BadRequest, Unauthorized
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler,
                          Filters, MessageHandler, run_async)
from telegram.utils.helpers import mention_html

REPORT_GROUP = 12
REPORT_IMMUNE_USERS = DRAGONS + TIGERS + WOLVES


@run_async
@user_admin
def report_setting(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                msg.reply_text(
                    "Raporlama açıldı! Herhangi biri bir şey bildirdiğinde bilgilendirileceksiniz."
                )

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                msg.reply_text(
                    "Raporlama kapatıldı! Herhangi bir rapor almayacaksınız.")
        else:
            msg.reply_text(
                f"Mevcut rapor tercihiniz: `{sql.user_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN)

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text(
                    "Raporlama açıldı! Raporları etkinleştiren yöneticiler, /report edildiklerinde bilgilendirilecekler "
                    "veya @admin çağrılır.")

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text(
                    "Raporlama kapatıldı! /report veya @admin ile ilgili hiçbir yönetici bilgilendirilmeyecek."
                )
        else:
            msg.reply_text(
                f"Bu grubun mevcut ayarı: `{sql.chat_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN)


@run_async
@user_not_admin
@loggable
def report(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()
        message = update.effective_message

        if not args:
            message.reply_text("Önce bildirmek için bir neden ekleyin.")
            return ""

        if user.id == reported_user.id:
            message.reply_text("Ah evet, Elbette ... çok mu?")
            return ""

        if user.id == bot.id:
            message.reply_text("İyi deneme.")
            return ""

        if reported_user.id in REPORT_IMMUNE_USERS:
            message.reply_text("Ah? Bir felaketi mi bildiriyorsunuz?")
            return ""

        if chat.username and chat.type == Chat.SUPERGROUP:

            reported = f"{mention_html(user.id, user.first_name)} reported {mention_html(reported_user.id, reported_user.first_name)} to the admins!"

            msg = (
                f"<b>⚠️ Rapor: </b>{html.escape(chat.title)}\n"
                f"<b> • Rapor ölçütü:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
                f"<b> • bildirilen kullanıcı:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
            )
            link = f'<b> • Bildirilen mesaj:</b> <a href="https://t.me/{chat.username}/{message.reply_to_message.message_id}">click here</a>'
            should_forward = False
            keyboard = [
                [
                    InlineKeyboardButton(
                        u"➡ Mesaj",
                        url=f"https://t.me/{chat.username}/{message.reply_to_message.message_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        u"⚠ Tekme",
                        callback_data=f"report_{chat.id}=kick={reported_user.id}={reported_user.first_name}"
                    ),
                    InlineKeyboardButton(
                        u"⛔️ Ban",
                        callback_data=f"report_{chat.id}=banned={reported_user.id}={reported_user.first_name}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        u"❎ Mesajı Sil",
                        callback_data=f"report_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reported = f"{mention_html(user.id, user.first_name)} reported " \
                       f"{mention_html(reported_user.id, reported_user.first_name)} to the admins!"

            msg = f'{mention_html(user.id, user.first_name)} is calling for admins in "{html.escape(chat_name)}"!'
            link = ""
            should_forward = True

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    if not chat.type == Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(
                                    message.text.split()
                            ) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)
                    if not chat.username:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(
                                    message.text.split()
                            ) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                    if chat.username and chat.type == Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup)

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if len(
                                    message.text.split()
                            ) > 1:  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    LOGGER.exception("Kullanıcıyı bildirirken istisna")

        message.reply_to_message.reply_text(
            f"{mention_html(user.id, user.first_name)} reported the message to the admins.",
            parse_mode=ParseMode.HTML)
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    return f"Bu sohbet aracılığıyla /report ve @admin yöneticileri için kullanıcı raporlarını göndermek için kurulum vardır: `{sql.chat_should_report(chat_id)}`"


def __user_settings__(user_id):
    if sql.user_should_report(user_id) is True:
        text = "Yönettiğiniz sohbetlerden raporlar alacaksınız."
    else:
        text = "Yönettiğiniz sohbetlerden *rapor* almayacaksınız."
    return text


def buttons(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    splitter = query.data.replace("report_", "").split("=")
    if splitter[1] == "Tekme":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            bot.unbanChatMember(splitter[0], splitter[2])
            query.answer("✅ Başarılı bir şekilde atıldı")
            return ""
        except Exception as err:
            query.answer("🛑 Delme Başarısız")
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML)
    elif splitter[1] == "yasaklandı":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            query.answer("✅  Başarıyla Yasaklandı")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"hata: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML)
            query.answer("🛑 Yasaklanamadı")
    elif splitter[1] == "sil":
        try:
            bot.deleteMessage(splitter[0], splitter[3])
            query.answer("✅ Mesaj Silindi")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"hata: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML)
            query.answer("🛑 Mesaj silinemedi!")


__help__ = """
 • `/report <neden>`*:* bir mesajı yöneticilerine bildirmek için yanıtla.
 • `@admin`*:* yöneticilere bildirmek için bir mesajı yanıtlayın.
*NOT:* Yöneticiler tarafından kullanıldığında bunların hiçbiri tetiklenmeyecektir.

*Yalnızca yöneticiler:*
 • `/reports <on/off>`*:* rapor ayarını değiştirin veya mevcut durumu görüntüleyin.
   • Öğleden sonra yapılırsa, durumunuzu değiştirir.
   • Grup içindeyse, o grupların durumunu değiştirir.
"""

SETTING_HANDLER = CommandHandler("reports", report_setting)
REPORT_HANDLER = CommandHandler("report", report, filters=Filters.group)
ADMIN_REPORT_HANDLER = MessageHandler(Filters.regex(r"(?i)@admin(s)?"), report)

REPORT_BUTTON_USER_HANDLER = CallbackQueryHandler(buttons, pattern=r"report_")
dispatcher.add_handler(REPORT_BUTTON_USER_HANDLER)

dispatcher.add_handler(SETTING_HANDLER)
dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)

__mod_name__ = "Reporting"
__handlers__ = [(REPORT_HANDLER, REPORT_GROUP),
                (ADMIN_REPORT_HANDLER, REPORT_GROUP), (SETTING_HANDLER)]
