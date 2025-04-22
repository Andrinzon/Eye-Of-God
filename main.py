import logging
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    JobQueue,
)
import datetime as dt

TOKEN = "6696093539:AAGY4X7KiIrtsGnZlhGcGkpStOG5fEwBDrk"
AUTO_ALERT_CHAT_ID = None  # Lo capturaremos automáticamente al usar /start

ALTCOINS = {
    "SOL": "solana",
    "BNB": "binancecoin",
    "ADA": "cardano",
    "XRP": "ripple"
}
BTC_ID = "bitcoin"

# --- Obtener cambio de precio en % en últimos minutos ---
async def fetch_price_change(coin_id, minutes=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": 1, "interval": "minutely"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            prices = data["prices"][-minutes:]
            if not prices: return 0
            old_price = prices[0][1]
            new_price = prices[-1][1]
            change = ((new_price - old_price) / old_price) * 100
            return round(change, 2)

# --- Detectar oportunidades basadas en rezago vs BTC ---
async def analizar_oportunidades():
    btc_change = await fetch_price_change(BTC_ID)
    if abs(btc_change) < 2:
        return None

    oportunidades = []
    for nombre, coin_id in ALTCOINS.items():
        alt_change = await fetch_price_change(coin_id)
        rezago = btc_change - alt_change

        if btc_change > 0 and alt_change < 0.5:
            oportunidades.append((nombre, alt_change, rezago))

    return btc_change, oportunidades

# --- Alerta automática cada hora ---
async def radar_automatico(context: ContextTypes.DEFAULT_TYPE):
    global AUTO_ALERT_CHAT_ID
    if AUTO_ALERT_CHAT_ID is None:
        return  # No se ha registrado ningún usuario todavía

    resultado = await analizar_oportunidades()
    if not resultado:
        return

    btc_change, oportunidades = resultado
    if not oportunidades:
        return

    msg = f"📡 Radar automático:\n🚨 BTC se movió {btc_change}% en 30 min.\n"
    msg += "🧠 Altcoins rezagadas detectadas:\n"
    for nombre, alt_change, rezago in oportunidades:
        confianza = "✅ Alta" if rezago > 1.5 else "🟡 Media"
        msg += f"• {nombre}: {alt_change}% ({confianza})\n"

    await context.bot.send_message(chat_id=AUTO_ALERT_CHAT_ID, text=msg)

# --- Comando /start con menú de botones ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_ALERT_CHAT_ID
    AUTO_ALERT_CHAT_ID = update.effective_chat.id  # Guardamos el chat ID

    keyboard = [
        [InlineKeyboardButton("📡 Radar de Oportunidades", callback_data="radar")],
        [InlineKeyboardButton("📉 Riesgo BTC", callback_data="riesgo")],
        [InlineKeyboardButton("🛑 Parar Bot", callback_data="parar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Bienvenido al bot Ojo de Dios 👁️. ¿Qué deseas hacer?",
        reply_markup=reply_markup
    )

# --- Botón del radar manual ---
async def boton_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "radar":
        await query.edit_message_text("🔍 Analizando mercado... por favor espera...")

        resultado = await analizar_oportunidades()
        if not resultado:
            await query.edit_message_text("📊 BTC no ha tenido un movimiento fuerte recientemente.")
            return

        btc_change, oportunidades = resultado
        if not oportunidades:
            await query.edit_message_text("⚠️ No se detectaron altcoins rezagadas por ahora.")
            return

        msg = f"🚨 BTC se movió {btc_change}% en 30 minutos.\n"
        msg += "🧠 Altcoins rezagadas detectadas:\n"
        for nombre, alt_change, rezago in oportunidades:
            confianza = "✅ Alta" if rezago > 1.5 else "🟡 Media"
            msg += f"• {nombre}: {alt_change}% ({confianza})\n"

        await query.edit_message_text(msg)

# --- Comando /parar ---
async def parar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 Bot detenido. Usa /start para activarlo nuevamente.")

# --- MAIN ---
async def post_init(app):
    app.job_queue.run_repeating(radar_automatico, interval=3600, first=30)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("parar", parar))
    app.add_handler(CallbackQueryHandler(boton_callback))

    print("Bot ejecutándose automáticamente...")
    app.run_polling()
