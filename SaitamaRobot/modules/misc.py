from SaitamaRobot.modules.helper_funcs.chat_status import user_admin
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot import dispatcher

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode, Update
from telegram.ext.dispatcher import run_async
from telegram.ext import CallbackContext, Filters, CommandHandler

MARKDOWN_HELP = f"""
Markdown telegram tarafından desteklenen çok güçlü bir biçimlendirme aracıdır. {dispatcher.bot.first_name} emin olmak için bazı geliştirmelere sahiptir \
kaydedilen mesajlar doğru şekilde ayrıştırılır ve düğmeler oluşturmanıza izin verir.

• <code>_italic_</code>: metni '_' ile kaydırmak italik metin üretecektir
• <code>*bold*</code>:  metni '*' ile kaydırmak kalın metin üretecektir
• <code>`code`</code>: '`' ile metin kaydırmak,'kod' olarak da bilinen tek aralıklı metin üretir
• <code>[sometext](someURL)</code>: bu bir bağlantı oluşturacaktır - mesaj sadece <code>birkaç metni</code> gösterecektir, \
ve üzerine dokunduğunuzda sayfa <code>someURL</code> adresinde açılacaktır.
<b>Example:</b><code>[test](example.com)</code>

• <code>[buttontext](buttonurl:someURL)</code>: bu, kullanıcıların telegram almasına izin veren özel bir geliştirmedir \
kendi markdown'larında düğmeler. <code>Düğmemetni</code> düğmede görüntülenen şey olacaktır ve <code>someurl</code> \
açılan url olacaktır.
<b>Örnek:</b> <code>[Bu bir düğmedir](buttonurl:example.com)</code>

Aynı satırda birden fazla düğme istiyorsanız, şu şekilde kullanın: aynı:
<code>[Bir](buttonurl://example.com)
[İki](buttonurl://google.com:same)</code>
Bu, her satırda bir düğme yerine tek bir satırda iki düğme oluşturacaktır.

Mesajınızın bir düğmeden başka bir metin içermesi <b>ZORUNLUDUR</b> !
"""


@run_async
@user_admin
def echo(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(
            args[1], parse_mode="MARKDOWN", disable_web_page_preview=True)
    else:
        message.reply_text(
            args[1],
            quote=False,
            parse_mode="MARKDOWN",
            disable_web_page_preview=True)
    message.delete()


def markdown_help_sender(update: Update):
    update.effective_message.reply_text(
        MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Aşağıdaki iletiyi bana iletmeyi deneyin, göreceksiniz #test!"
    )
    update.effective_message.reply_text(
        "/save test Bu bir indirim testidir test. _italics_, *bold*, code, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)")


@run_async
def markdown_help(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        update.effective_message.reply_text(
            'Öğleden sonra bana ulaşın',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "Markdown help",
                    url=f"t.me/{context.bot.username}?start=markdownhelp")
            ]]))
        return
    markdown_help_sender(update)


__help__ = """
*Kullanılabilir komutlar:*
*Markdown:*
 • `/markdownhelp`*:* işaretlemenin telgrafta nasıl çalıştığının hızlı özeti - yalnızca özel sohbetlerde çağrılabilir
*Paste:*
 • `/paste`*:* Yanıtlanan içeriği `nekobin.com` a kaydeder ve bir url ile yanıtlar
*Tepki:*
 • `/react`*:* Rastgele bir reaksiyonla tepki verir 
*Kent Sözlüğü:*
 • `/ud <word>`*:* Kullanmak istediğiniz kelimeyi veya ifadeyi yazın
*Wikipedia:*
 • `/wiki <query>`*:* sorgunuz wikipedia
*Duvar kağıtları:*
 • `/wall <query>`*:* duvar kağıdı alın
*Döviz Çevirici:* 
 • `/cash`*:* para birimi dönüştürücü
Örnek:
 `/cash 1 USD INR`  
      _OR_
 `/cash 1 usd inr`
Output: `1.0 USD = 75.505 INR`
"""

ECHO_HANDLER = DisableAbleCommandHandler("echo", echo, filters=Filters.group)
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help)

dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)

__mod_name__ = "Extras"
__command_list__ = ["id", "echo"]
__handlers__ = [
    ECHO_HANDLER,
    MD_HELP_HANDLER,
]
