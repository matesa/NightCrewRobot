import sre_constants

import regex
import telegram
from SaitamaRobot import LOGGER, dispatcher
from SaitamaRobot.modules.disable import DisableAbleMessageHandler
from SaitamaRobot.modules.helper_funcs.regex_helper import (infinite_loop_check)
from telegram import Update
from telegram.ext import CallbackContext, Filters, run_async

DELIMITERS = ("/", ":", "|", "_")


def separate_sed(sed_string):
    if len(sed_string) >= 3 and sed_string[
            1] in DELIMITERS and sed_string.count(sed_string[1]) >= 2:
        delim = sed_string[1]
        start = counter = 2
        while counter < len(sed_string):
            if sed_string[counter] == "\\":
                counter += 1

            elif sed_string[counter] == delim:
                replace = sed_string[start:counter]
                counter += 1
                start = counter
                break

            counter += 1

        else:
            return None

        while counter < len(sed_string):
            if sed_string[counter] == "\\" and counter + 1 < len(
                    sed_string) and sed_string[counter + 1] == delim:
                sed_string = sed_string[:counter] + sed_string[counter + 1:]

            elif sed_string[counter] == delim:
                replace_with = sed_string[start:counter]
                counter += 1
                break

            counter += 1
        else:
            return replace, sed_string[start:], ""

        flags = ""
        if counter < len(sed_string):
            flags = sed_string[counter:]
        return replace, replace_with, flags.lower()


@run_async
def sed(update: Update, context: CallbackContext):
    sed_result = separate_sed(update.effective_message.text)
    if sed_result and update.effective_message.reply_to_message:
        if update.effective_message.reply_to_message.text:
            to_fix = update.effective_message.reply_to_message.text
        elif update.effective_message.reply_to_message.caption:
            to_fix = update.effective_message.reply_to_message.caption
        else:
            return

        repl, repl_with, flags = sed_result
        if not repl:
            update.effective_message.reply_to_message.reply_text(
                "De??i??tirmeye ??al??????yorsun... "
                "bir ??ey yok mu?")
            return

        try:
            try:
                check = regex.match(
                    repl, to_fix, flags=regex.IGNORECASE, timeout=5)
            except TimeoutError:
                return
            if check and check.group(0).lower() == to_fix.lower():
                update.effective_message.reply_to_message.reply_text(
                    "Herkese merhaba, {} yapmaya ??al??????yor "
                    "istemedi??im ??eyler s??yl??yorum "
                    "s??yle!".format(update.effective_user.first_name))
                return
            if infinite_loop_check(repl):
                update.effective_message.reply_text(
                    "Korkar??m bu normal ifadeyi ??al????t??ram??yorum.")
                return
            if 'i' in flags and 'g' in flags:
                text = regex.sub(
                    repl, repl_with, to_fix, flags=regex.I, timeout=3).strip()
            elif 'i' in flags:
                text = regex.sub(
                    repl, repl_with, to_fix, count=1, flags=regex.I,
                    timeout=3).strip()
            elif 'g' in flags:
                text = regex.sub(repl, repl_with, to_fix, timeout=3).strip()
            else:
                text = regex.sub(
                    repl, repl_with, to_fix, count=1, timeout=3).strip()
        except TimeoutError:
            update.effective_message.reply_text('Timeout')
            return
        except sre_constants.error:
            LOGGER.warning(update.effective_message.text)
            LOGGER.exception("SRE sabit hatas??")
            update.effective_message.reply_text(
                "Hatta yat??yor musun? G??r??n????e g??re de??il.")
            return

        # empty string errors -_-
        if len(text) >= telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(
                "Sed komutunun sonucu \
                                                 telegram!")
        elif text:
            update.effective_message.reply_to_message.reply_text(text)


__help__ = """
 ??? `s/<text1>/<text2>(/<flag>)`*:* Bu mesaj ??zerinde bir sed i??lemi ger??ekle??tirmek i??in bir mesaj?? bununla yan??tlay??n, t??m??n?? \ de??i??tirerek
occurrences of 'metin1' ile 'metin2'. nin tekrarlar??. Bayraklar iste??e ba??l??d??r ve ??u anda b??y??k, / k??????k harflerin yoksay??lmas?? i??in 'i', global i??in 'g', \
veya hi??bir??ey. S??n??rlay??c??lar aras??nda `/`, `_`, `|`, ve `:`. bulunur. Metin gruplama desteklenmektedir. Ortaya ????kan mesaj olamaz \
daha geni?? {}.
*Hat??rlatma:* Sed, e??le??tirmeyi kolayla??t??rmak i??in baz?? ??zel karakterler kullan??r, ??rne??in: `+*.?\\`
Bu karakterleri kullanmak istiyorsan??z, onlardan ka??t??????n??zdan emin olun!
*??rnek:* \\?.
""".format(telegram.MAX_MESSAGE_LENGTH)

__mod_name__ = "Sed/Regex"

SED_HANDLER = DisableAbleMessageHandler(
    Filters.regex(r's([{}]).*?\1.*'.format("".join(DELIMITERS))),
    sed,
    friendly="sed")

dispatcher.add_handler(SED_HANDLER)
