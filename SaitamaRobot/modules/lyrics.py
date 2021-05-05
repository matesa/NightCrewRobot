from tswift import Song

from telegram import Bot, Update, Message, Chat
from telegram.ext import run_async

from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler


@run_async
def lyrics(bot: Bot, update: Update, args):
    msg = update.effective_message
    query = " ".join(args)
    song = ""
    if not query:
        msg.reply_text("Hangi şarkıyı arayacağınızı belirtmediniz!")
        return
    else:
        song = Song.find_song(query)
        if song:
            if song.lyrics:
                reply = song.format()
            else:
                reply = "Bu şarkı için herhangi bir şarkı sözü bulunamadı!"
        else:
            reply = "Şarkı bulunamadı!"
        if len(reply) > 4090:
            with open("lyrics.txt", 'w') as f:
                f.write(f"{reply}\n\n\nOwO UwU OmO")
            with open("lyrics.txt", 'rb') as f:
                msg.reply_document(document=f,
                caption="Mesaj uzunluğu maksimum sınırı aştı! Metin dosyası olarak gönderiliyor.")
        else:
            msg.reply_text(reply)

__help__ = """
En sevdiğiniz şarkıların sözlerini doğrudan uygulamadan mı almak istiyorsunuz? Bu modül bunun için mükemmel!
*Kullanılabilir komutlar:*
 - /lyrics <song>: o şarkının sözlerini döndürür.
 Yalnızca şarkı adını veya hem sanatçı hem de şarkı adını girebilirsiniz.
"""


__mod_name__ = "Lyrics"
                
        


LYRICS_HANDLER = DisableAbleCommandHandler("lyrics", lyrics, pass_args=True)

dispatcher.add_handler(LYRICS_HANDLER)
