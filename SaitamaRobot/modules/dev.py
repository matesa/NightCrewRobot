import os
import subprocess
import sys
from time import sleep

from SaitamaRobot import dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import dev_plus
from telegram import TelegramError, Update
from telegram.ext import CallbackContext, CommandHandler, run_async


@run_async
@dev_plus
def leave(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        try:
            bot.leave_chat(int(chat_id))
            update.effective_message.reply_text("Bip boop, o çorbayı bıraktım!.")
        except TelegramError:
            update.effective_message.reply_text(
                "Bip sesi, bu gruptan ayrılamadım (neden olduğunu bilmiyorum).")
    else:
        update.effective_message.reply_text("Geçerli bir sohbet kimliği gönderin")


@run_async
@dev_plus
def gitpull(update: Update, context: CallbackContext):
    sent_msg = update.effective_message.reply_text(
        "Uzaktan kumandadan tüm değişiklikleri çekip yeniden başlatmaya çalışıyorum.")
    subprocess.Popen('git pull', stdout=subprocess.PIPE, shell=True)

    sent_msg_text = sent_msg.text + "\n\nDeğişiklikler alındı ​​... Sanırım .. Yeniden başlatılıyor "

    for i in reversed(range(5)):
        sent_msg.edit_text(sent_msg_text + str(i + 1))
        sleep(1)

    sent_msg.edit_text("Yeniden Başlatıldı.")

    os.system('restart.bat')
    os.execv('start.bat', sys.argv)


@run_async
@dev_plus
def restart(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        "Yeni bir örnek başlatmak ve bunu kapatmak")

    os.system('restart.bat')
    os.execv('start.bat', sys.argv)


LEAVE_HANDLER = CommandHandler("leave", leave)
GITPULL_HANDLER = CommandHandler("gitpull", gitpull)
RESTART_HANDLER = CommandHandler("reboot", restart)

dispatcher.add_handler(LEAVE_HANDLER)
dispatcher.add_handler(GITPULL_HANDLER)
dispatcher.add_handler(RESTART_HANDLER)

__mod_name__ = "Dev"
__handlers__ = [LEAVE_HANDLER, GITPULL_HANDLER, RESTART_HANDLER]
