import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes, CallbackQueryHandler

TELEGRAM_TOKEN = "7463495309:AAFnWbMN8eYShhTt9UvygCD0TAFED-LuJhM"  # Pon tu token aquí

logging.basicConfig(level=logging.INFO)

# Función para obtener el precio de BTC
def obtener_precio(moneda):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={moneda}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[moneda]["usd"] if moneda in data else None
    except Exception:
        return None

# Función para calcular el riesgo de BTC
def calcular_riesgo_btc():
    try:
        # Obtener el precio de BTC
        precio_inicial = obtener_precio("bitcoin")
        if precio_inicial is None:
            return "❌ Error: No se pudo obtener el precio de BTC."

        # Obtener el precio de BTC hace 7 días
        precio_final = obtener_precio("bitcoin")
        if precio_final is None:
            return "❌ Error: No se pudo obtener el precio de BTC."

        # Calcular la volatilidad
        volatilidad = (precio_final - precio_inicial) / precio_inicial

        return {
            "riesgo": volatilidad,
            "confianza": max(0.0, 1 - volatilidad),
            "volatilidad": volatilidad,
        }
    
    except Exception as e:
        return f"❌ Error desconocido: {str(e)}"

# Función para formatear el mensaje de riesgo
def formatear_mensaje(resultado):
    return (
        f"🧐 *Riesgo BTC:* {resultado['riesgo']:.4f}\n"
        f"🟢 *Confianza:* {resultado['confianza']:.2f}\n"
        f"📉 *Volatilidad:* {resultado['volatilidad']:.4f}"
    )

# Comando de inicio
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    resultado = calcular_riesgo_btc()
    if isinstance(resultado, str):  # Si el resultado es un error en cadena
        mensaje = resultado
    else:
        mensaje = "👁‍🗨 *Eye of God Activado*\n\n" + formatear_mensaje(resultado)

    keyboard = [
        [InlineKeyboardButton("🔍 Ver Riesgo", callback_data="riesgo")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [InlineKeyboardButton("🛑 Parar Alertas", callback_data="parar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)

# Comando para ver el riesgo manualmente
async def riesgo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = calcular_riesgo_btc()
    if isinstance(resultado, str):  # Si el resultado es un error en cadena
        mensaje = resultado
    else:
        mensaje = formatear_mensaje(resultado)

    await update.message.reply_text(mensaje, parse_mode='Markdown')

# Comando de información
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = "🧠 *Eye of God* calcula el riesgo de BTC basándose en la volatilidad de su precio.\n"
    mensaje += "Un mayor riesgo indica más incertidumbre en el mercado.\n"
    mensaje += "🧮 Fórmula utilizada: `riesgo = volatilidad`\n"
    await update.message.reply_text(mensaje, parse_mode='Markdown')

# Comando para parar alertas
async def parar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in jobs:
        job.schedule_removal()
    await update.message.reply_text("🛑 Alertas automáticas detenidas.")

# Manejador de botones
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "riesgo":
        resultado = calcular_riesgo_btc()
        mensaje = formatear_mensaje(resultado) if isinstance(resultado, dict) else resultado
        await query.edit_message_text(mensaje, parse_mode='Markdown')
    elif data == "info":
        await query.edit_message_text(
            "🧮 Fórmula usada: `riesgo = volatilidad`",
            parse_mode='Markdown'
        )
    elif data == "parar":
        chat_id = query.message.chat_id
        jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in jobs:
            job.schedule_removal()
        await query.edit_message_text("🛑 Alertas automáticas desactivadas.")

# Función principal para ejecutar el bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("riesgo", riesgo))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("parar", parar))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Eye of God corriendo en Telegram...")
    app.run_polling()

if __name__ == "__main__":
    main()
