import asyncio
from asyncio import sleep

from telethon import events
from telethon.errors import ChatAdminRequiredError, UserAdminInvalidError
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsAdmins

from SaitamaRobot import telethn, OWNER_ID, DEV_USERS, DRAGONS, TIGERS

# =================== CONSTANT ===================

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)


UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

OFFICERS = [OWNER_ID] + DEV_USERS + DRAGONS + TIGERS

# Check if user has admin rights
async def is_administrator(user_id: int, message):
    admin = False
    async for user in telethn.iter_participants(
        message.chat_id, filter=ChannelParticipantsAdmins
    ):
        if user_id == user.id or user_id in OFFICERS:
            admin = True
            break
    return admin



@telethn.on(events.NewMessage(pattern=f"^[!/]zombies ?(.*)"))
async def zombies(event):
    """ .zombies komutu için, bir sohbette tüm zombileri listeleyin. """

    con = event.pattern_match.group(1).lower()
    del_u = 0
    del_status = "Silinmiş Hesap Bulunamadı, Grup Temiz."

    if con != "clean":
        find_zombies = await event.respond("Zombiler Aranıyor...")
        async for user in event.client.iter_participants(event.chat_id):

            if user.deleted:
                del_u += 1
                await sleep(1)
        if del_u > 0:
            del_status = f"Bulundu **{del_u}** Bu Grupta Zombiler.\
            \nŞunları Kullanarak Temizleyin :-\n 👉 `/zombies clean`"
        await find_zombies.edit(del_status)
        return

    # Here laying the sanity check
    chat = await event.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    
    if not await is_administrator(user_id=event.from_id, message=event):
        await event.respond("Yönetici Değilsin!")
        return
    
    if not admin and not creator:
        await event.respond("Burada Yönetici Değilim!")
        return

    cleaning_zombies = await event.respond("Zombileri Temizliyor...")
    del_u = 0
    del_a = 0

    async for user in event.client.iter_participants(event.chat_id):
        if user.deleted:
            try:
                await event.client(
                    EditBannedRequest(event.chat_id, user.id, BANNED_RIGHTS)
                )
            except ChatAdminRequiredError:
                await cleaning_zombies.edit("Bu Grupta Yasaklama Hakkım Yok.")
                return
            except UserAdminInvalidError:
                del_u -= 1
                del_a += 1
            await event.client(EditBannedRequest(event.chat_id, user.id, UNBAN_RIGHTS))
            del_u += 1

    if del_u > 0:
        del_status = f"Temizlendi `{del_u}` Zombiler"

    if del_a > 0:
        del_status = f"Temizlendi `{del_u}` Zombiler \
        \n`{del_a}` Zombi Yönetici Hesapları Kaldırılmadı!"

    await cleaning_zombies.edit(del_status)
