# Created by @p_rinc_e
from pathlib import Path
import asyncio, time, io, math, os, logging, asyncio, shutil, re, subprocess, json
from re import findall
from asyncio import sleep
from telethon.events import NewMessage
from telethon.tl.custom import Dialog
from datetime import datetime as dt
from pytz import country_names as c_n, country_timezones as c_tz, timezone as tz
from hachoir.parser import createParser
import pybase64
from base64 import b64decode
from pySmartDL import SmartDL
from telethon.tl.types import DocumentAttributeVideo, DocumentAttributeAudio
from telethon import events

from SaitamaRobot.event import register
from SaitamaRobot.utils import progress
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.messages import ImportChatInviteRequest as Get
from validators.url import url
from html import unescape
from urllib.error import HTTPError
import bs4
from bs4 import BeautifulSoup
from youtube_dl import YoutubeDL

from youtube_dl.utils import (DownloadError, ContentTooShortError,

                              ExtractorError, GeoRestrictedError,
                              MaxDownloadsReached, PostProcessingError,
                              UnavailableVideoError, XAttrMetadataError)

try:

   from youtubesearchpython import SearchVideos 

except:
	os.system("pip install pip install youtube-search-python")
	from youtubesearchpython import SearchVideos 
	pass

@register(pattern="^/song (.*)")
async def download_video(v_url):

    lazy = v_url ; sender = await lazy.get_sender() ; me = await lazy.client.get_me()

    if not sender.id == me.id:
        rkp = await lazy.reply("`işleniyor...`")
    else:
    	rkp = await lazy.edit("`işleniyor...`")   
    url = v_url.pattern_match.group(1)
    if not url:
         return await rkp.edit("`Hatar \nkullanım song <şarkı adı>`")
    search = SearchVideos(url, offset = 1, mode = "json", max_results = 1)
    test = search.result()
    p = json.loads(test)
    q = p.get('search_result')
    try:
       url = q[0]['link']
    except:
    	return await rkp.edit("`bulunamadı`")
    type = "audio"
    await rkp.edit("`İndirmeye hazırlanılıyor...`")
    if type == "audio":
        opts = {
            'format':
            'bestaudio',
            'addmetadata':
            True,
            'key':
            'FFmpegMetadata',
            'writethumbnail':
            True,
            'prefer_ffmpeg':
            True,
            'geo_bypass':
            True,
            'nocheckcertificate':
            True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'outtmpl':
            '%(id)s.mp3',
            'quiet':
            True,
            'logtostderr':
            False
        }
        video = False
        song = True    
    try:
        await rkp.edit("`Veriler alınıyor, lütfen bekleyin..`")
        with YoutubeDL(opts) as rip:
            rip_data = rip.extract_info(url)
    except DownloadError as DE:
        await rkp.edit(f"`{str(DE)}`")
        return
    except ContentTooShortError:
        await rkp.edit("`İndirilen içerik çok kısaydı.`")
        return
    except GeoRestrictedError:
        await rkp.edit(
            "`Video, bir web sitesi tarafından uygulanan coğrafi kısıtlamalar nedeniyle coğrafi konumunuzda kullanılamıyor.`"
        )
        return
    except MaxDownloadsReached:
        await rkp.edit("`Azami indirme sınırına ulaşıldı.`")
        return
    except PostProcessingError:
        await rkp.edit("`İşlem sonrası bir hata oluştu.`")
        return
    except UnavailableVideoError:
        await rkp.edit("`Medya, istenen formatta mevcut değil.`")
        return
    except XAttrMetadataError as XAME:
        await rkp.edit(f"`{XAME.code}: {XAME.msg}\n{XAME.reason}`")
        return
    except ExtractorError:
        await rkp.edit("`Bilgi alma sırasında bir hata oluştu..`")
        return
    except Exception as e:
        await rkp.edit(f"{str(type(e)): {str(e)}}")
        return
    c_time = time.time()
    if song:
        await rkp.edit(f"`Şarkıyı yüklemeye hazırlanıyor:`\
        \n**{rip_data['title']}**\
        \nby *{rip_data['uploader']}*")
        await v_url.client.send_file(
            v_url.chat_id,
            f"{rip_data['id']}.mp3",
            supports_streaming=True,
            attributes=[
                DocumentAttributeAudio(duration=int(rip_data['duration']),
                                       title=str(rip_data['title']),
                                       performer=str(rip_data['uploader']))
            ],
            progress_callback=lambda d, t: asyncio.get_event_loop(
            ).create_task(
                progress(d, t, v_url, c_time, "Yükleniyor..",
                         f"{rip_data['title']}.mp3")))
        os.remove(f"{rip_data['id']}.mp3")
    elif video:
        await rkp.edit(f"`Şarkıyı yüklemeye hazırlanıyor :`\
        \n**{rip_data['title']}**\
        \nby *{rip_data['uploader']}*")
        await v_url.client.send_file(
            v_url.chat_id,
            f"{rip_data['id']}.mp4",
            supports_streaming=True,
            caption=url,
            progress_callback=lambda d, t: asyncio.get_event_loop(
            ).create_task(
                progress(d, t, v_url, c_time, "Yükleniyor..",
                         f"{rip_data['title']}.mp4")))
        os.remove(f"{rip_data['id']}.mp4")


@register(pattern="^/video (.*)")
async def download_video(v_url):  
    lazy = v_url ; sender = await lazy.get_sender() ; me = await lazy.client.get_me()
    if not sender.id == me.id:
        rkp = await lazy.reply("`işleniyor...`")
    else:
    	rkp = await lazy.edit("`işleniyor...`")   
    url = v_url.pattern_match.group(1)
    if not url:
         return await rkp.edit("`Hata \nkullanım song <şarkı adı>`")
    search = SearchVideos(url, offset = 1, mode = "json", max_results = 1)
    test = search.result()
    p = json.loads(test)
    q = p.get('search_result')
    try:
       url = q[0]['link']
    except:
    	return await rkp.edit("`bulunamadı`")
    type = "audio"
    await rkp.edit("`İndirmeye hazırlanılıyor...`")
    if type == "audio":
        opts = {
            'format':
            'best',
            'addmetadata':
            True,
            'key':
            'FFmpegMetadata',
            'prefer_ffmpeg':
            True,
            'geo_bypass':
            True,
            'nocheckcertificate':
            True,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }],
            'outtmpl':
            '%(id)s.mp4',
            'logtostderr':
            False,
            'quiet':
            True
        }
        song = False
        video = True
    try:
        await rkp.edit("`Veriler alınıyor, lütfen bekleyin..`")
        with YoutubeDL(opts) as rip:
            rip_data = rip.extract_info(url)
    except DownloadError as DE:
        await rkp.edit(f"`{str(DE)}`")
        return
    except ContentTooShortError:
        await rkp.edit("`İndirilen içerik çok kısaydı.`")
        return
    except GeoRestrictedError:
        await rkp.edit(
            "`Video, bir web sitesi tarafından uygulanan coğrafi kısıtlamalar nedeniyle coğrafi konumunuzda kullanılamıyor.`"
        )
        return
    except MaxDownloadsReached:
        await rkp.edit("`Azami indirme sınırına ulaşıldı.`")
        return
    except PostProcessingError:
        await rkp.edit("`İşlem sonrası bir hata oluştu.`")
        return
    except UnavailableVideoError:
        await rkp.edit("`Medya, istenen formatta mevcut değil.`")
        return
    except XAttrMetadataError as XAME:
        await rkp.edit(f"`{XAME.code}: {XAME.msg}\n{XAME.reason}`")
        return
    except ExtractorError:
        await rkp.edit("`Bilgi alma sırasında bir hata oluştu.`")
        return
    except Exception as e:
        await rkp.edit(f"{str(type(e)): {str(e)}}")
        return
    c_time = time.time()
    if song:
        await rkp.edit(f"`Şarkıyı yüklemeye hazırlanılıyor `\
        \n**{rip_data['title']}**\
        \nby *{rip_data['uploader']}*")
        await v_url.client.send_file(
            v_url.chat_id,
            f"{rip_data['id']}.mp3",
            supports_streaming=True,
            attributes=[
                DocumentAttributeAudio(duration=int(rip_data['duration']),
                                       title=str(rip_data['title']),
                                       performer=str(rip_data['uploader']))
            ],
            progress_callback=lambda d, t: asyncio.get_event_loop(
            ).create_task(
                progress(d, t, v_url, c_time, "Yükleniyor..",
                         f"{rip_data['title']}.mp3")))
        os.remove(f"{rip_data['id']}.mp3")
        await v_url.delete()
    elif video:
        await rkp.edit(f"`Video şarkıyı yüklemeye hazırlanıyor :`\
        \n**{rip_data['title']}**\
        \nby *{rip_data['uploader']}*")
        await v_url.client.send_file(
            v_url.chat_id,
            f"{rip_data['id']}.mp4",
            supports_streaming=True,
            caption=rip_data['title'],
            progress_callback=lambda d, t: asyncio.get_event_loop(
            ).create_task(
                progress(d, t, v_url, c_time, "Yükleniyor..",
                         f"{rip_data['title']}.mp4")))
        os.remove(f"{rip_data['id']}.mp4")
        await rkp.delete()


__help__ = """
 ➩ /song <şarkıcı(isteğe bağlı)>: şarkıyı mevcut en iyi kalitede yükler

 ➩ /video <şarkıcı(isteğe bağlı)>: video şarkısını mevcut en iyi kalitede yükler
"""

__mod_name__ = "Songs"