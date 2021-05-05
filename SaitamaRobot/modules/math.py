import math

import pynewtonmath as newton
from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from telegram import Update
from telegram.ext import CallbackContext, run_async


@run_async
def simplify(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.simplify('{}'.format(args[0])))


@run_async
def factor(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.factor('{}'.format(args[0])))


@run_async
def derive(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.derive('{}'.format(args[0])))


@run_async
def integrate(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.integrate('{}'.format(args[0])))


@run_async
def zeroes(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.zeroes('{}'.format(args[0])))


@run_async
def tangent(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.tangent('{}'.format(args[0])))


@run_async
def area(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.area('{}'.format(args[0])))


@run_async
def cos(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(math.cos(int(args[0])))


@run_async
def sin(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(math.sin(int(args[0])))


@run_async
def tan(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(math.tan(int(args[0])))


@run_async
def arccos(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(math.acos(int(args[0])))


@run_async
def arcsin(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(math.asin(int(args[0])))


@run_async
def arctan(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(math.atan(int(args[0])))


@run_async
def abs(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(math.fabs(int(args[0])))


@run_async
def log(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    message.reply_text(math.log(int(args[0])))


__help__ = """
karmaşık matematik problemlerini çözer
 • `/math`*:* Math `/math 2^2+2(2)`
 • `/factor`*:* Factor `/factor x^2 + 2x`
 • `/derive`*:* Derive `/derive x^2+2x`
 • `/integrate`*:* Integrate `/integrate x^2+2x`
 • `/zeroes`*:* Find 0's `/zeroes x^2+2x`
 • `/tangent`*:* Find Tangent `/tangent 2lx^3`
 • `/area`*:* Area Under Curve `/area 2:4lx^3`
 • `/cos`*:* Cosine `/cos pi`
 • `/sin`*:* Sine `/sin 0`
 • `/tan`*:* Tangent `/tan 0`
 • `/arccos`*:* Inverse Cosine `/arccos 1`
 • `/arcsin`*:* Inverse Sine `/arcsin 0`
 • `/arctan`*:* Inverse Tangent `/arctan 0`
 • `/abs`*:* Absolute Value `/abs -1`
 • `/log`*:* Logarithm `/log 2l8`

_Belirli bir x değerinde bir fonksiyonun teğet çizgisini bulmak için, isteği c | f (x) olarak gönderin; burada c, verilen x değeri ve f (x), fonksiyon ifadesidir, ayırıcı bir dikeydir çubuğu '|'. Örnek bir talep için yukarıdaki tabloya bakın.
Bir fonksiyonun altındaki alanı bulmak için, isteği c: d | f (x) olarak gönderin; burada c başlangıç ​​x değeri, d bitiş x değeri ve f (x), altında eğri olmasını istediğiniz fonksiyondur. iki x değeri.
Kesirleri hesaplamak için, payda (üzeri) payda olarak ifadeleri girin. Örneğin, 2 / 4'ü işlemek için ifadenizi 2 (fazla) 4 olarak göndermelisiniz. Sonuç ifadesi standart matematik gösterimi (1/2, 3/4) olacaktır.
"""

__mod_name__ = "Math"

SIMPLIFY_HANDLER = DisableAbleCommandHandler("math", simplify)
FACTOR_HANDLER = DisableAbleCommandHandler("factor", factor)
DERIVE_HANDLER = DisableAbleCommandHandler("derive", derive)
INTEGRATE_HANDLER = DisableAbleCommandHandler("integrate", integrate)
ZEROES_HANDLER = DisableAbleCommandHandler("zeroes", zeroes)
TANGENT_HANDLER = DisableAbleCommandHandler("tangent", tangent)
AREA_HANDLER = DisableAbleCommandHandler("area", area)
COS_HANDLER = DisableAbleCommandHandler("cos", cos)
SIN_HANDLER = DisableAbleCommandHandler("sin", sin)
TAN_HANDLER = DisableAbleCommandHandler("tan", tan)
ARCCOS_HANDLER = DisableAbleCommandHandler("arccos", arccos)
ARCSIN_HANDLER = DisableAbleCommandHandler("arcsin", arcsin)
ARCTAN_HANDLER = DisableAbleCommandHandler("arctan", arctan)
ABS_HANDLER = DisableAbleCommandHandler("abs", abs)
LOG_HANDLER = DisableAbleCommandHandler("log", log)

dispatcher.add_handler(SIMPLIFY_HANDLER)
dispatcher.add_handler(FACTOR_HANDLER)
dispatcher.add_handler(DERIVE_HANDLER)
dispatcher.add_handler(INTEGRATE_HANDLER)
dispatcher.add_handler(ZEROES_HANDLER)
dispatcher.add_handler(TANGENT_HANDLER)
dispatcher.add_handler(AREA_HANDLER)
dispatcher.add_handler(COS_HANDLER)
dispatcher.add_handler(SIN_HANDLER)
dispatcher.add_handler(TAN_HANDLER)
dispatcher.add_handler(ARCCOS_HANDLER)
dispatcher.add_handler(ARCSIN_HANDLER)
dispatcher.add_handler(ARCTAN_HANDLER)
dispatcher.add_handler(ABS_HANDLER)
dispatcher.add_handler(LOG_HANDLER)
