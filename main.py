import logging
import requests
import statistics
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes,
    CallbackQueryHandler
)

TELEGRAM_TOKEN = "6696093539:AAGY4X7KiIrtsGnZlhGcGkpStOG5fEwBDrk"

logging.basicConfig(level=logging.INFO)

# ================================
# FUNCIONES DE RIESGO Y ANÁLISIS
# ================================
def calcular_riesgo_btc():
    try:
        history_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        history_params = {"vs_currency": "usd", "days": "7", "interval": "hourly"}
        history_data = requests.get(history_url, params=history_params).json()
        precios = [p[1] for p in history_data["prices"]]
        cambios_pct = [(precios[i + 1] - precios[i]) / precios[i] for i in range(len(precios) - 1)]
        volatilidad = statistics.stdev(cambios_pct)

        info_btc = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin").json()
        sentimiento_negativo = info_btc["sentiment_votes_down_percentage"] / 100

        global_data = requests.get("https://api.coingecko.com/api/v3/global").json()
        dominancia_btc = global_data["data"]["market_cap_percentage"]["btc"] / 100

        confianza = max(0.0, 1 - min(volatilidad * 100, 1))
        riesgo = (1 - confianza) * volatilidad * (1 + sentimiento_negativo) * (1 + dominancia_btc)

        return {
            "riesgo": riesgo,
            "confianza": confianza,
            "volatilidad": volatilidad,
            "sentimiento_negativo": sentimiento_negativo,
            "dominancia_btc": dominancia_btc
        }
    except Exception as e:
        return {"error": str(e)}

def formatear_mensaje(resultado):
    riesgo = resultado['riesgo']
    if riesgo > 1.5:
        estado = "🚨 *Alto riesgo* – Precaución"
    elif riesgo < 0.7:
        estado = "✅ *Bajo riesgo* – Posible oportunidad"
    else:
        estado = "⚠️ *Riesgo moderado*"

    return (
        f"{estado}\n\n"
        f"*Riesgo BTC:* `{riesgo:.4f}`\n"
        f"*Confianza:* `{resultado['confianza']:.2f}`\n"
        f"*Volatilidad:* `{resultado['volatilidad']:.4f}`\n"
        f"*Sentimiento Negativo:* `{resultado['sentimiento_negativo']:.2f}`\n"
        f"*Dominancia BTC:* `{resultado['dominancia_btc']:.2f}`"
    )

# ================================
# FUNCIONES BOT
# ================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.chat_data['chat_id'] = chat_id

    # Enviar mensaje inicial
    resultado = calcular_riesgo_btc()
    if "error" not in resultado:
        mensaje = "👁‍🗨 *Eye of God Activado*\n\n" + formatear_mensaje(resultado)
    else:
        mensaje = "❌ Error al iniciar: " + resultado['error']

    # Menú de botones
    keyboard = [
        [InlineKeyboardButton("🔍 Ver Riesgo", callback_data="riesgo")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [InlineKeyboardButton("🛑 Parar Alertas", callback_data="parar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)

    # Activar alertas automáticas
    context.job_queue.run_repeating(
        enviar_alerta, interval=3600, first=3600, chat_id=chat_id, name=str(chat_id)
    )

async def riesgo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = calcular_riesgo_btc()
    if "error" not in resultado:
        mensaje = formatear_mensaje(resultado)
    else:
        mensaje = "❌ Error al obtener datos: " + resultado['error']

    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "👁 *Eye of God* es un bot que evalúa el riesgo de invertir en BTC usando la fórmula de Bierak:\n\n"
        "`riesgo = (1 - confianza) * volatilidad * (1 + sentimiento_negativo) * (1 + dominancia_btc)`\n\n"
        "Valores bajos de riesgo pueden indicar oportunidades. Valores altos sugieren precaución."
    )
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def parar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in jobs:
        job.schedule_removal()

    await update.message.reply_text("🛑 Alertas detenidas.")

# ================================
# FUNCIONES PARA BOTONES INLINE
# ================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "riesgo":
        resultado = calcular_riesgo_btc()
        if "error" not in resultado:
            mensaje = formatear_mensaje(resultado)
        else:
            mensaje = "❌ Error al obtener datos: " + resultado['error']
        await query.edit_message_text(text=mensaje, parse_mode='Markdown')
    elif query.data == "info":
        mensaje = (
            "👁 *Eye of God* evalúa el riesgo BTC con la fórmula de Bierak:\n"
            "`riesgo = (1 - confianza) * volatilidad * (1 + sentimiento_negativo) * (1 + dominancia_btc)`"
        )
        await query.edit_message_text(text=mensaje, parse_mode='Markdown')
    elif query.data == "parar":
        chat_id = query.message.chat_id
        jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in jobs:
            job.schedule_removal()
        await query.edit_message_text("🛑 Alertas automáticas desactivadas.")

# ================================
# ENVÍO AUTOMÁTICO
# ================================
async def enviar_alerta(context: CallbackContext):
    chat_id = context.job.chat_id
    resultado = calcular_riesgo_btc()
    if "error" not in resultado:
        mensaje = "⏰ *Alerta automática de riesgo BTC*\n\n" + formatear_mensaje(resultado)
    else:
        mensaje = "❌ Error al calcular riesgo automático: " + resultado['error']

    await context.bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown')

# ================================
# MAIN
# ================================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("riesgo", riesgo))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("parar", parar))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Eye of God en funcionamiento...")
    app.run_polling()

if __name__ == "__main__":
    main()
