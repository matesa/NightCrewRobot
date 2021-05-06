import datetime
from typing import List

import requests
from SaitamaRobot import TIME_API_KEY, dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async


def generate_time(to_find: str, findtype: List[str]) -> str:
    data = requests.get(
        f"https://api.timezonedb.com/v2.1/list-time-zone"
        f"?key={TIME_API_KEY}"
        f"&format=json"
        f"&fields=countryCode,countryName,zoneName,gmtOffset,timestamp,dst"
    ).json()

    for zone in data["zones"]:
        for eachtype in findtype:
            if to_find in zone[eachtype].lower():
                country_name = zone['countryName']
                country_zone = zone['zoneName']
                country_code = zone['countryCode']

                if zone['dst'] == 1:
                    daylight_saving = "Yes"
                else:
                    daylight_saving = "No"

                date_fmt = r"%d-%m-%Y"
                time_fmt = r"%H:%M:%S"
                day_fmt = r"%A"
                gmt_offset = zone['gmtOffset']
                timestamp = datetime.datetime.now(
                    datetime.timezone.utc) + datetime.timedelta(
                        seconds=gmt_offset)
                current_date = timestamp.strftime(date_fmt)
                current_time = timestamp.strftime(time_fmt)
                current_day = timestamp.strftime(day_fmt)

                break

    try:
        result = (
            f'<b>Ülke:</b> <code>{country_name}</code>\n'
            f'<b>Bölge Adı:</b> <code>{country_zone}</code>\n'
            f'<b>Ülke Kodu:</b> <code>{country_code}</code>\n'
            f'<b>Gün ışığından yararlanma:</b> <code>{daylight_saving}</code>\n'
            f'<b>Gün:</b> <code>{current_day}</code>\n'
            f'<b>Şimdiki Zaman:</b> <code>{current_time}</code>\n'
            f'<b>Geçerli Tarih:</b> <code>{current_date}</code>\n'
            '<b>Saat Dilimleri:</b> <a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones">Buraya yazın</a>'
        )
    except:
        result = None

    return result


@run_async
def gettime(update: Update, context: CallbackContext):
    message = update.effective_message

    try:
        query = message.text.strip().split(" ", 1)[1]
    except:
        message.reply_text(
            "Bulmak için bir ülke adı/abbreviation/timezone dilimi sağlayın.")
        return
    send_message = message.reply_text(
        f"için saat dilimi bilgisi bulunuyor <b>{query}</b>", parse_mode=ParseMode.HTML )

    query_timezone = query.lower()
    if len(query_timezone) == 2:
        result = generate_time(query_timezone, ["Ülke Kodu"])
    else:
        result = generate_time(query_timezone, ["bölgeAdı", "ülkeAdı"])

    if not result:
        send_message.edit_text(
            f'Timezone bilgisi <b>{query}</b> için mevcut değil\n'
            '<b>Tüm Zaman Dilimleri:</b> <a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones">List here</a>',
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True)
        return

    send_message.edit_text(
        result, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


__help__ = """
 • `/time <query>`*:* Bir saat dilimi hakkında bilgi verir.

*Mevcut sorgular:* Ülke Kodu/Ülke Adı/Saat Dilimi Adı
• 🕐 [Zaman dilimleri listesi](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
"""

TIME_HANDLER = DisableAbleCommandHandler("time", gettime)

dispatcher.add_handler(TIME_HANDLER)

__mod_name__ = "Time"
__command_list__ = ["time"]
__handlers__ = [TIME_HANDLER]
