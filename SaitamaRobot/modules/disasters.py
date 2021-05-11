import html
import json
import os
from typing import Optional

from SaitamaRobot import (DEV_USERS, OWNER_ID, DRAGONS, SUPPORT_CHAT, DEMONS,
                          TIGERS, WOLVES, dispatcher)
from SaitamaRobot.modules.helper_funcs.chat_status import (dev_plus, sudo_plus,
                                                           whitelist_plus)
from SaitamaRobot.modules.helper_funcs.extraction import extract_user
from SaitamaRobot.modules.log_channel import gloggable
from telegram import ParseMode, TelegramError, Update
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html

ELEVATED_USERS_FILE = os.path.join(os.getcwd(),
                                   'SaitamaRobot/elevated_users.json')


def check_user_id(user_id: int, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    if not user_id:
        reply = "Bu ... bir sohbet?"

    elif user_id == bot.id:
        reply = "Bu, bu şekilde çalışmaz."

    else:
        reply = None
    return reply


# This can serve as a deeplink example.
#disasters =
# """ Text here """

# do not async, not a handler
#def send_disasters(update):
#    update.effective_message.reply_text(
#        disasters, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

### Deep link example ends

#FtSasaki adding add to pro developer cmd :D

@run_async
@dev_plus
@gloggable
def addpiro(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)
        
    if int(user_id) in DEV_USERS:
      message.reply_text("Bu üye zaten bir Pro Geliştirici")
        
    if user_id in DRAGONS:
        rt += "HQ'dan bir Dragon Felaketini Pro Geliştiriciye yükseltmesi istendi."
        data['sudos'].remove(user_id)
        DRAGONS.remove(user_id)

    if user_id in DEMONS:
        rt += "HQ'dan bir Demon Felaketini Pro Geliştiriciye yükseltmesi istendi."
        data['supports'].remove(user_id)
        DEMONS.remove(user_id)

    if user_id in WOLVES:
        rt += "HQ'dan Wolf Disaster'ı Pro Developer'a yükseltmesi istendi."
        data['whitelists'].remove(user_id)
        WOLVES.remove(user_id)

    data['devs'].append(user_id)
    DEV_USERS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + "\n{} Afet düzeyi başarıyla Pro Geliştirici olarak ayarlandı!".format(
            user_member.first_name))

    log_message = (
        f"#ProDeveloper\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@dev_plus
@gloggable
def addsudo(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        message.reply_text("Bu üye zaten bir Dragon Felaketi")
        return ""

    if user_id in DEMONS:
        rt += "HA'dan, İblis Felaketini Ejderhaya yükseltmesi istendi."
        data['supports'].remove(user_id)
        DEMONS.remove(user_id)

    if user_id in WOLVES:
        rt += "HA'dan bir Kurt Felaketini Ejderhaya yükseltmesi istendi."
        data['whitelists'].remove(user_id)
        WOLVES.remove(user_id)

    data['sudos'].append(user_id)
    DRAGONS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + "\n{} Afet düzeyi başarıyla Dragon olarak ayarlandı!".format(
            user_member.first_name))

    log_message = (
        f"#SUDO\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@sudo_plus
@gloggable
def addsupport(
    update: Update,
    context: CallbackContext,
) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        rt += "HA'nın bu Ejderhayı İblis'e indirgemesi istendi"
        data['sudos'].remove(user_id)
        DRAGONS.remove(user_id)

    if user_id in DEMONS:
        message.reply_text("Bu kullanıcı zaten bir Demon Felaketidir.")
        return ""

    if user_id in WOLVES:
        rt += "Bu Kurt Felaketini İblis'e yükseltmek için HA istendi"
        data['whitelists'].remove(user_id)
        WOLVES.remove(user_id)

    data['supports'].append(user_id)
    DEMONS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + f"\n{user_member.first_name} bir Demon Felaketi olarak eklendi!")

    log_message = (
        f"#SUPPORT\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@sudo_plus
@gloggable
def addwhitelist(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        rt += "Bu üye bir Ejderha Felaketi, Kurt'a Düşürülüyor."
        data['sudos'].remove(user_id)
        DRAGONS.remove(user_id)

    if user_id in DEMONS:
        rt += "Bu kullanıcı zaten bir Demon Felaketi, Wolf'a İndiriliyor."
        data['supports'].remove(user_id)
        DEMONS.remove(user_id)

    if user_id in WOLVES:
        message.reply_text("Bu kullanıcı zaten bir Kurt Felaketi.")
        return ""

    data['whitelists'].append(user_id)
    WOLVES.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt +
        f"\n{user_member.first_name} başarıyla Kurt Felaketine yükseltildi!")

    log_message = (
        f"#WHITELIST\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))} \n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@run_async
@sudo_plus
@gloggable
def addtiger(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        rt += "Bu üye bir Dragon Felaketidir, Tiger'a Düşürüyor."
        data['sudos'].remove(user_id)
        DRAGONS.remove(user_id)

    if user_id in DEMONS:
        rt += "Bu kullanıcı zaten bir Demon Felaketi, Tiger'a Düşürülüyor."
        data['supports'].remove(user_id)
        DEMONS.remove(user_id)

    if user_id in WOLVES:
        rt += "Bu kullanıcı zaten bir Kurt Felaketi, Tiger'a İndiriliyor."
        data['whitelists'].remove(user_id)
        WOLVES.remove(user_id)

    if user_id in TIGERS:
        message.reply_text("Bu kullanıcı zaten bir Tiger.")
        return ""

    data['tigers'].append(user_id)
    TIGERS.append(user_id)

    with open(ELEVATED_USERS_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt +
        f"\n{user_member.first_name} başarıyla Tiger Felaketine yükseltildi!"
    )

    log_message = (
        f"#TIGER\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))} \n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != 'private':
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message

#FtSasaki adding rmpiro to remove user from {devs}
@run_async
@dev_plus
@gloggable
def rmpiro(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in DEV_USERS:
        message.reply_text("Karargahın bu kullanıcıyı Civilian statüsüne düşürmesi istendi")
        DEV_USERS.remove(user_id)
        data['devs'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNDEV\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != 'private':
            log_message = "<b>{}:</b>\n".format(html.escape(
                chat.title)) + log_message

        return log_message

    else:
        message.reply_text("Bu kullanıcı bir Pro Developer Felaketi değil!")
        return ""
      
      
@run_async
@dev_plus
@gloggable
def removesudo(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in DRAGONS:
        message.reply_text("HA'nın bu kullanıcıyı Sivil düzeyine düşürmesi istendi")
        DRAGONS.remove(user_id)
        data['sudos'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNSUDO\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != 'private':
            log_message = "<b>{}:</b>\n".format(html.escape(
                chat.title)) + log_message

        return log_message

    else:
        message.reply_text("Bu kullanıcı bir Dragon Felaketi değil!")
        return ""


@run_async
@sudo_plus
@gloggable
def removesupport(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in DEMONS:
        message.reply_text("HA'nın bu kullanıcıyı Sivil düzeyine düşürmesi istendi")
        DEMONS.remove(user_id)
        data['supports'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNSUPPORT\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != 'private':
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message

    else:
        message.reply_text("Bu kullanıcı İblis seviyesinde bir Felaket değil!")
        return ""


@run_async
@sudo_plus
@gloggable
def removewhitelist(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in WOLVES:
        message.reply_text("Normal kullanıcıya indirgenme")
        WOLVES.remove(user_id)
        data['whitelists'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNWHITELIST\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != 'private':
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        message.reply_text("Bu kullanıcı bir Kurt Felaketi değil!")
        return ""


@run_async
@sudo_plus
@gloggable
def removetiger(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, 'r') as infile:
        data = json.load(infile)

    if user_id in TIGERS:
        message.reply_text("Normal kullanıcıya indirgenme")
        TIGERS.remove(user_id)
        data['tigers'].remove(user_id)

        with open(ELEVATED_USERS_FILE, 'w') as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNTIGER\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != 'private':
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        message.reply_text("Bu kullanıcı bir Tiger Felaketi değil!")
        return ""


@run_async
@whitelist_plus
def whitelistlist(update: Update, context: CallbackContext):
    reply = "<b>Bilinen Kurt Felaketleri 🐺:</b>\n"
    bot = context.bot
    for each_user in WOLVES:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)

            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def tigerlist(update: Update, context: CallbackContext):
    reply = "<b>Bilinen Kaplan Afetleri 🐯:</b>\n"
    bot = context.bot
    for each_user in TIGERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def supportlist(update: Update, context: CallbackContext):
    bot = context.bot
    reply = "<b>Bilinen Demon Afetler 👹:</b>\n"
    for each_user in DEMONS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def sudolist(update: Update, context: CallbackContext):
    bot = context.bot
    true_sudo = list(set(DRAGONS) - set(DEV_USERS))
    reply = "<b>Bilinen Ejderha Felaketleri 🐉:</b>\n"
    for each_user in true_sudo:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def devlist(update: Update, context: CallbackContext):
    bot = context.bot
    true_dev = list(set(DEV_USERS) - {OWNER_ID})
    reply = "<b>Kahraman Derneği Üyeleri ⚡️:</b>\n"
    for each_user in true_dev:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            reply += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


__help__ = f"""
*⚠️ Uyarı:*
Burada listelenen komutlar yalnızca özel erişime sahip kullanıcılar için çalışır, çoğunlukla sorun giderme, hata ayıklama amacıyla kullanılır.
Grup yöneticilerinin /grup sahiplerinin bu komutlara ihtiyacı yoktur. 

 ╔ *Tüm özel kullanıcıları listeleyin:*
 ╠ `/dragons`*:* Tüm Dragon felaketlerini listeler
 ╠ `/demons`*:* Tüm Demon felaketlerini listeler
 ╠ `/tigers`*:* Tüm Kaplan felaketlerini listeler
 ╠ `/wolves`*:* Tüm Kurt felaketlerini listeler
 ╠ `/heroes`*:* Tüm Hero Association üyelerini listeler
 ╠ `/adddragon`*:* Dragon'a bir kullanıcı ekler
 ╠ `/adddemon`*:* Demon'a bir kullanıcı ekler
 ╠ `/addtiger`*:* Tiger'a bir kullanıcı ekler
 ╠ `/addwolf`*:* Wolf'a bir kullanıcı ekler
 ╚ `Dev ekle mevcut değil, geliştiriciler kendilerini nasıl ekleyeceklerini bilmeli`

 ╔ *Ping:*
 ╠ `/ping`*:* botun telegram sunucusuna ping süresini alır
 ╚ `/pingall`*:* listelenen tüm ping sürelerini alır

 ╔ *Yayın: (Yalnızca bot sahibi)*
 ╠  *Note:* Bu, temel indirimi destekler
 ╠ `/broadcastall`*:* Her yerde yayın yapar
 ╠ `/broadcastusers`*:* Tüm kullanıcıları da yayınlar
 ╚ `/broadcastgroups`*:* Tüm grupları da yayınlar

 ╔ *Grup Bilgileri:*
 ╠ `/groups`*:* Grupları İsim, Kimlik ile listeleyin, üyeler bir txt olarak sayılır
 ╠ `/leave <ID>`*:* Gruptan ayrılın, ID kısa çizgiye sahip olmalıdır
 ╠ `/stats`*:* Genel bot istatistiklerini gösterir
 ╠ `/getchats`*:* Kullanıcının görüldüğü grup adlarının bir listesini alır. Yalnızca bot sahibi
 ╚ `/ginfo username/link/ID`*:* Tüm grup için bilgi panelini çeker

╔ *Erişim kontrolü:* 
 ╠ `/ignore`*:* Bir kullanıcıyı kara listeye alır 
 ╠  botu tamamen kullanmak
 ╠ `/notice`*:* Kullanıcıyı kara listeden çıkarır
 ╚ `/ignoredlist`*:* Göz ardı edilen kullanıcıları listeler

 ╔ *Modül yükleme:*
 ╠ `/listmodules`*:* Modülleri ve adlarını yazdırır
 ╠ `/unload <name>`*:* Modülü dinamik olarak kaldırır
 ╚ `/load <name>`*:* Yük modülü

 ╔ *Hız Testi:*
 ╚ `/speedtest`*:* En hızlı testi çalıştırır ve size metin veya görüntü çıkışı arasından seçim yapabileceğiniz 2 seçenek sunar
 ╔ *Genel Yasaklar:*
 ╠ `/gban user reason`*:* Bir kullanıcıyı genel olarak yasaklar
 ╚ `/ungban user reason`*:* Kullanıcıyı genel yasak listesinden kaldırır

 ╔ *Modül yükleme:*
 ╠ `/listmodules`*:* Tüm modüllerin adlarını listeler
 ╠ `/load modulename`*:* Söz konusu modülü  
 ╠   yeniden başlatmadan bellek.
 ╠ `/unload modulename`*:* Söz konusu modülü
 ╚   yeniden başlatmadan bellek. Botu yeniden başlatmadan bellek  

 ╔ *Uzaktan komutlar:*
 ╠ `/rban user group`*:* Uzaktan yasaklama
 ╠ `/runban user group`*:* Uzaktan yasaklama kaldırma
 ╠ `/rpunch user group`*:* Uzaktan delme
 ╠ `/rmute user group`*:* Uzaktan sessiz
 ╚ `/runmute user group`*:* Uzaktan sessiz açma


 ╔ *Yalnızca Windows kendi kendine barındırılır:*
 ╠ `/reboot`*:* Bot hizmetini yeniden başlatır
 ╚ `/gitpull`*:* Depoyu çeker ve bot hizmetini yeniden başlatır

 ╔ *Sohbet Robotu:* 
 ╚ `/listaichats`*:* Sohbet modunun etkin olduğu sohbetleri listeler
 
 ╔ *Hata Ayıklama ve Kabuk:* 
 ╠ `/debug <on/off>`*:* Komutları update.txt dosyasına kaydeder
 ╠ `/logs`*:* Günlükleri öğleden sonra almak için bunu destek grubunda çalıştırın
 ╠ `/eval`*:* Kendinden açıklamalı
 ╠ `/sh`*:* Kabuk komutunu çalıştırır
 ╠ `/shell`*:* Kabuk komutunu çalıştırır
 ╠ `/clearlocals`*:* Adından da anlaşılacağı gibi
 ╠ `/dbcleanup`*:* Silinen kayıtları ve grupları veritabanından kaldırır
 ╚ `/py`*:* Python kodunu çalıştırır
 
 ╔ *Genel Yasaklar:*
 ╠ `/gban <id> <reason>`*:* Kullanıcıyı Gbans, yanıtla da çalışır
 ╠ `/ungban`*:* Kullanıcıyı ungbans, gban ile aynı kullanım
 ╚ `/gbanlist`*:* Yasaklı kullanıcıların listesini çıkarır

Daha fazla bilgi için @{SUPPORT_CHAT} adresini ziyaret edin.
"""

DEV_HANDLER = CommandHandler(("addpiro", "addsudo"), addpiro)
SUDO_HANDLER = CommandHandler(("addsudo", "adddragon"), addsudo)
SUPPORT_HANDLER = CommandHandler(("addsupport", "adddemon"), addsupport)
TIGER_HANDLER = CommandHandler(("addtiger"), addtiger)
WHITELIST_HANDLER = CommandHandler(("addwhitelist", "addwolf"), addwhitelist)

RMPIRO_HANDLER = CommandHandler(("rmpiro", "removesudo"), rmpiro)
UNSUDO_HANDLER = CommandHandler(("removesudo", "removedragon"), removesudo)
UNSUPPORT_HANDLER = CommandHandler(("removesupport", "removedemon"),
                                   removesupport)
UNTIGER_HANDLER = CommandHandler(("removetiger"), removetiger)
UNWHITELIST_HANDLER = CommandHandler(("removewhitelist", "removewolf"),
                                     removewhitelist)

WHITELISTLIST_HANDLER = CommandHandler(["whitelistlist", "wolves"],
                                       whitelistlist)
TIGERLIST_HANDLER = CommandHandler(["tigers"], tigerlist)
SUPPORTLIST_HANDLER = CommandHandler(["supportlist", "demons"], supportlist)
SUDOLIST_HANDLER = CommandHandler(["sudolist", "dragons"], sudolist)
DEVLIST_HANDLER = CommandHandler(["devlist", "heroes"], devlist)

dispatcher.add_handler(DEV_HANDLER)
dispatcher.add_handler(SUDO_HANDLER)
dispatcher.add_handler(SUPPORT_HANDLER)
dispatcher.add_handler(TIGER_HANDLER)
dispatcher.add_handler(WHITELIST_HANDLER)
dispatcher.add_handler(UNSUDO_HANDLER)
dispatcher.add_handler(UNSUPPORT_HANDLER)
dispatcher.add_handler(UNTIGER_HANDLER)
dispatcher.add_handler(UNWHITELIST_HANDLER)

dispatcher.add_handler(RMPIRO_HANDLER)
dispatcher.add_handler(WHITELISTLIST_HANDLER)
dispatcher.add_handler(TIGERLIST_HANDLER)
dispatcher.add_handler(SUPPORTLIST_HANDLER)
dispatcher.add_handler(SUDOLIST_HANDLER)
dispatcher.add_handler(DEVLIST_HANDLER)

__mod_name__ = "Disasters"
__handlers__ = [
    DEV_HANDLER, SUDO_HANDLER, SUPPORT_HANDLER, TIGER_HANDLER, WHITELIST_HANDLER,
    RMPIRO_HANDLER, UNSUDO_HANDLER, UNSUPPORT_HANDLER, UNTIGER_HANDLER, UNWHITELIST_HANDLER,
    WHITELISTLIST_HANDLER, TIGERLIST_HANDLER, SUPPORTLIST_HANDLER,
    SUDOLIST_HANDLER, DEVLIST_HANDLER
]
