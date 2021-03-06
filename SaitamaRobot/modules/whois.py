from datetime import datetime

from pyrogram import filters
from pyrogram.types import User, Message
from pyrogram.raw import functions
from pyrogram.errors import PeerIdInvalid
from SaitamaRobot import pbot

def ReplyCheck(message: Message):
    reply_id = None

    if message.reply_to_message:
        reply_id = message.reply_to_message.message_id

    elif not message.from_user.is_self:
        reply_id = message.message_id

    return reply_id

infotext = (
    "**[{full_name}](tg://user?id={user_id})**\n"
    " * Kullanıcı Kimliği: `{user_id}`\n"
    " * Adı: `{first_name}`\n"
    " * Soyadı: `{last_name}`\n"
    " * Kullanıcı adı: `{username}`\n"
    " * Son Çevrimiçi: `{last_online}`\n"
    " * Bio: {bio}")

def LastOnline(user: User):
    if user.is_bot:
        return ""
    elif user.status == 'Yakın zamanda':
        return "Yakın zamanda"
    elif user.status == 'hafta içinde':
        return "Geçen hafta içinde"
    elif user.status == 'ay içinde':
        return "Geçen ay içinde"
    elif user.status == 'Uzun zaman önce':
        return "Uzun zaman önce :("
    elif user.status == 'çevrimiçi':
        return "Şuan çevrimiçi"
    elif user.status == 'çevrimdışı':
        return datetime.fromtimestamp(user.status.date).strftime("%a, %d %b %Y, %H:%M:%S")


def FullName(user: User):
    return user.first_name + " " + user.last_name if user.last_name else user.first_name

@pbot.on_message(filters.command('whois'))
async def whois(client, message):
    cmd = message.command
    if not message.reply_to_message and len(cmd) == 1:
        get_user = message.from_user.id
    elif len(cmd) == 1:
        get_user = message.reply_to_message.from_user.id
    elif len(cmd) > 1:
        get_user = cmd[1]
        try:
            get_user = int(cmd[1])
        except ValueError:
            pass
    try:
        user = await client.get_users(get_user)
    except PeerIdInvalid:
        await message.reply("O Kullanıcıyı bilmiyorum.")
        return
    desc = await client.get_chat(get_user)
    desc = desc.description
    await message.reply_text(
            infotext.format(
                full_name=FullName(user),
                user_id=user.id,
                user_dc=user.dc_id,
                first_name=user.first_name,
                last_name=user.last_name if user.last_name else "",
                username=user.username if user.username else "",
                last_online=LastOnline(user),
                bio=desc if desc else "`Biyo kurulum yok.`"),
            disable_web_page_preview=True)
