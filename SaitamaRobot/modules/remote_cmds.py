from SaitamaRobot import dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import (
    bot_admin, is_bot_admin, is_user_ban_protected, is_user_in_chat)
from SaitamaRobot.modules.helper_funcs.extraction import extract_user_and_text
from SaitamaRobot.modules.helper_funcs.filters import CustomFilters
from telegram import Update, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async

RBAN_ERRORS = {
    "Kullanıcı sohbetin yöneticisidir", "Sohbet bulunamadı",
    "Sohbet üyesini /kısıtlamak için yeterli hak yok",
    "User_not_participant", "Peer_id_invalid", "Grup sohbeti devre dışı bırakıldı",
    "Basit bir gruptan yumruk atmak için bir kullanıcının davetlisi olmalı",
    "Chat_admin_required",
    "Yalnızca temel bir grubu oluşturan kişi grup yöneticilerini yumruklayabilir",
    "Channel_private", "Sohbette yok"
}

RUNBAN_ERRORS = {
    "Kullanıcı sohbetin yöneticisidir", "Sohbet bulunamadı",
    "Sohbet üyesini /kısıtlamak için yeterli hak yok",
    "User_not_participant", "Peer_id_invalid", "Grup sohbeti devre dışı bırakıldı",
    "Basit bir gruptan yumruk atmak için bir kullanıcının davetlisi olmalı",
    "Chat_admin_required",
    "Yalnızca temel bir grubu oluşturan kişi grup yöneticilerini yumruklayabilir",
    "Channel_private", "Sohbette yok"
}

RKICK_ERRORS = {
    "Kullanıcı sohbetin yöneticisidir", "Sohbet bulunamadı",
    "Sohbet üyesini /kısıtlamak için yeterli hak yok",
    "User_not_participant", "Peer_id_invalid", "Grup sohbeti devre dışı bırakıldı",
    "Basit bir gruptan yumruk atmak için bir kullanıcının davetlisi olmalı",
    "Chat_admin_required",
    "Yalnızca temel bir grubu oluşturan kişi grup yöneticilerini yumruklayabilir",
    "Channel_private", "Sohbette yok"
}

RMUTE_ERRORS = {
    "Kullanıcı sohbetin yöneticisidir", "Sohbet bulunamadı",
    "Sohbet üyesini /kısıtlamak için yeterli hak yok",
    "User_not_participant", "Peer_id_invalid", "Grup sohbeti devre dışı bırakıldı",
    "Basit bir gruptan yumruk atmak için bir kullanıcının davetlisi olmalı",
    "Chat_admin_required",
    "Yalnızca temel bir grubu oluşturan kişi grup yöneticilerini yumruklayabilir",
    "Channel_private", "Sohbette yok"
}

RUNMUTE_ERRORS = {
    "Kullanıcı sohbetin yöneticisidir", "Sohbet bulunamadı",
    "Sohbet üyesini /kısıtlamak için yeterli hak yok",
    "User_not_participant", "Peer_id_invalid", "Grup sohbeti devre dışı bırakıldı",
    "Basit bir gruptan yumruk atmak için bir kullanıcının davetlisi olmalı",
    "Chat_admin_required",
    "Yalnızca temel bir grubu oluşturan kişi grup yöneticilerini yumruklayabilir",
    "Channel_private", "Sohbette yok"
}


@run_async
@bot_admin
def rban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Bir sohbet /user kullanıcıyla ilgili görünmüyorsunuz.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Bir kullanıcıya atıfta bulunmuyorsunuz veya belirtilen kimlik yanlış.."
        )
        return
    elif not chat_id:
        message.reply_text("Bir sohbete atıfta bulunmuyorsunuz.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Sohbet Bulunmadı":
            message.reply_text(
                "Sohbet bulunamadı! Geçerli bir sohbet kimliği girdiğinizden emin olun ve ben de o sohbetin bir parçasıyım."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Üzgünüm ama bu özel bir sohbet!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "Oradaki insanları kısıtlayamam! Yönetici olduğumdan ve kullanıcıları yasaklayabildiğimden emin olun."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Yöneticileri yasaklayabilmeyi gerçekten çok isterdim...")
        return

    if user_id == bot.id:
        message.reply_text("Ben kendim BAN yapmayacağım, deli misin?")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("Sohbetten yasaklandı!")
    except BadRequest as excp:
        if excp.message == "Cevap mesajı bulunamadı":
            # Do not reply
            message.reply_text('Yasaklandı!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Lanet olsun, bu kullanıcıyı yasaklayamam.")


@run_async
@bot_admin
def runban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Bir sohbet /user kullanıcıyla ilgili görünmüyorsunuz.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Bir kullanıcıya atıfta bulunmuyorsunuz veya belirtilen kimlik yanlış.."
        )
        return
    elif not chat_id:
        message.reply_text("Bir sohbete atıfta bulunmuyorsunuz.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Sohbet bulunamadı":
            message.reply_text(
                "Sohbet bulunamadı! Geçerli bir sohbet kimliği girdiğinizden emin olun ve ben de o sohbetin bir parçasıyım."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Üzgünüm ama bu özel bir sohbet!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "Oradaki kişilerin kısıtlamasını kaldıramam! Yönetici olduğumdan ve kullanıcıların yasağını kaldırabileceğimden emin olun."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            message.reply_text("Bu kullanıcıyı orada bulamıyorum")
            return
        else:
            raise

    if is_user_in_chat(chat, user_id):
        message.reply_text(
            "Zaten o sohbette olan birinin yasağını neden uzaktan kaldırmaya çalışıyorsun?"
        )
        return

    if user_id == bot.id:
        message.reply_text("Ben de YASAKLAMAYI KALDIRMAYACAm , orada bir yöneticiyim!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Evet, bu kullanıcı o sohbete katılabilir!")
    except BadRequest as excp:
        if excp.message == "Cevap mesajı bulunamadı":
            # Do not reply
            message.reply_text('Unbanned!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                " %s sohbetinde %s (%s) kullanıcısının yasağı %s nedeniyle kaldırılıyor", user_id,
                chat.title, chat.id, excp.message)
            message.reply_text("Lanet olsun, bu kullanıcının yasağını kaldıramıyorum.")


@run_async
@bot_admin
def rkick(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Bir sohbet /user kullanıcıyla ilgili görünmüyorsunuz.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Bir kullanıcıya atıfta bulunmuyorsunuz veya belirtilen kimlik yanlış.."
        )
        return
    elif not chat_id:
        message.reply_text("Bir sohbete atıfta bulunmuyorsunuz.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Sohbet bulunamadı":
            message.reply_text(
                "Sohbet bulunamadı! Geçerli bir sohbet kimliği girdiğinizden emin olun ve ben de o sohbetin bir parçasıyım."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Üzgünüm ama bu özel bir sohbet!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "Oradaki insanları kısıtlayamam! Yönetici olduğumdan ve kullanıcıları yumruklayabildiğinden emin olun."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Yöneticileri yumruklayabilmeyi gerçekten çok isterdim...")
        return

    if user_id == bot.id:
        message.reply_text("Kendime yumruk atmayacağım , deli misin?")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Sohbetten çıktı!")
    except BadRequest as excp:
        if excp.message == "Cevap mesajı bulunamadı":
            # Do not reply
            message.reply_text('Punched!', quote=False)
        elif excp.message in RKICK_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("%s sohbetinde %s (%s) kullanıcıyı %s nedeniyle delme HATASI",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Lanet olsun, o kullanıcıyı yumruklayamam.")


@run_async
@bot_admin
def rmute(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Bir sohbet /user kullanıcıyla ilgili görünmüyorsunuz.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Bir kullanıcıya atıfta bulunmuyorsunuz veya belirtilen kimlik yanlış.."
        )
        return
    elif not chat_id:
        message.reply_text("Bir sohbete atıfta bulunmuyorsunuz.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Sohbet bulunamadı":
            message.reply_text(
                "Sohbet bulunamadı! Geçerli bir sohbet kimliği girdiğinizden emin olun ve ben de o sohbetin bir parçasıyım."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Üzgünüm ama bu özel bir sohbet!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "Oradaki kişileri kısıtlayamam! Yönetici olduğumdan ve kullanıcıların sesini kapatabildiğimden emin olun."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Gerçekten yöneticilerin sesini kapatabilmeyi dilerdim...")
        return

    if user_id == bot.id:
        message.reply_text("Kendimi de MUTE yapmayacağım, deli misin?")
        return

    try:
        bot.restrict_chat_member(
            chat.id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False))
        message.reply_text("Sohbette yoksayıldı!")
    except BadRequest as excp:
        if excp.message == "Cevap mesajı bulunamadı":
            # Do not reply
            message.reply_text('Muted!', quote=False)
        elif excp.message in RMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("%s sohbetinde %s kullanıcısının (%s) sesini %s nedeniyle hata",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Lanet olsun, bu kullanıcının sesini kapatamıyorum.")


@run_async
@bot_admin
def runmute(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Bir sohbet /user kullanıcıyla ilgili görünmüyorsunuz.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Bir kullanıcıya atıfta bulunmuyorsunuz veya belirtilen kimlik yanlış.."
        )
        return
    elif not chat_id:
        message.reply_text("Bir sohbete atıfta bulunmuyorsunuz.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Sohbet bulunamadı":
            message.reply_text(
                "Sohbet bulunamadı! Geçerli bir sohbet kimliği girdiğinizden emin olun ve ben de o sohbetin bir parçasıyım."
            )
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Üzgünüm ama bu özel bir sohbet!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(
            bot.id).can_restrict_members:
        message.reply_text(
            "Oradaki kişilerin kısıtlamasını kaldıramam! Yönetici olduğumdan ve kullanıcıların yasağını kaldırabileceğimden emin olun."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            message.reply_text("Bu kullanıcıyı orada bulamıyorum")
            return
        else:
            raise

    if is_user_in_chat(chat, user_id):
        if member.can_send_messages and member.can_send_media_messages \
           and member.can_send_other_messages and member.can_add_web_page_previews:
            message.reply_text(
                "Bu kullanıcının o sohbette konuşma hakkı zaten var.")
            return

    if user_id == bot.id:
        message.reply_text("Ben YOKSUZ ETMEYECEĞİM, orada bir yöneticiyim!")
        return

    try:
        bot.restrict_chat_member(
            chat.id,
            int(user_id),
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True))
        message.reply_text("Evet, bu kullanıcı o sohbette konuşabilir!")
    except BadRequest as excp:
        if excp.message == "Cevap mesajı bulunamadı":
            # Do not reply
            message.reply_text('Unmuted!', quote=False)
        elif excp.message in RUNMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "%s sohbetinde %s (%s) kullanıcısını yoksayma HATASI %s nedeniyle", user_id,
                chat.title, chat.id, excp.message)
            message.reply_text("Lanet olsun, bu kullanıcının sesini açamıyorum.")


RBAN_HANDLER = CommandHandler("rban", rban, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler(
    "runban", runban, filters=CustomFilters.sudo_filter)
RKICK_HANDLER = CommandHandler(
    "rpunch", rkick, filters=CustomFilters.sudo_filter)
RMUTE_HANDLER = CommandHandler(
    "rmute", rmute, filters=CustomFilters.sudo_filter)
RUNMUTE_HANDLER = CommandHandler(
    "runmute", runmute, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
dispatcher.add_handler(RKICK_HANDLER)
dispatcher.add_handler(RMUTE_HANDLER)
dispatcher.add_handler(RUNMUTE_HANDLER)
