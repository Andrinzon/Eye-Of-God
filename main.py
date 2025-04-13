import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackContext,
    CallbackQueryHandler,
)

# 🔐 Tu token de bot
TELEGRAM_TOKEN = "7463495309:AAFnWbMN8eYShhTt9UvygCD0TAFED-LuJhM"

# 📋 Configuración de logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# 📉 Obtener precio actual de una moneda
def obtener_precio(moneda):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={moneda}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[moneda]["usd"] if moneda in data else None
    except Exception:
        return None

# 🔍 Calcular riesgo usando una fórmula simple de volatilidad
def calcular_riesgo_btc():
    try:
        precio_inicial = obtener_precio("bitcoin")
        precio_final = obtener_precio("bitcoin")
        if precio_inicial is None or precio_final is None:
            return "❌ No se pudo obtener el precio de BTC."
        volatilidad = abs(precio_final - precio_inicial) / precio_inicial
        return {
            "riesgo": volatilidad,
            "confianza": max(0.0, 1 - volatilidad),
            "volatilidad": volatilidad,
        }
    except Exception as e:
        return f"❌ Error desconocido: {str(e)}"

# 🧾 Formatear resultados
def formatear_mensaje(resultado):
    return (
        f"🧐 *Riesgo BTC:* {resultado['riesgo']:.4f}\n"
        f"🟢 *Confianza:* {resultado['confianza']:.2f}\n"
        f"📉 *Volatilidad:* {resultado['volatilidad']:.4f}"
    )

# 🚀 Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = calcular_riesgo_btc()
    if isinstance(resultado, str):
        mensaje = resultado
    else:
        mensaje = "👁‍🗨 *Eye of God Activado*\n\n" + formatear_mensaje(resultado)

    keyboard = [
        [InlineKeyboardButton("🔍 Ver Riesgo", callback_data="riesgo")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
        [InlineKeyboardButton("🛑 Parar Alertas", callback_data="parar")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)

# 🔁 Botón "Ver Riesgo"
async def riesgo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = calcular_riesgo_btc()
    mensaje = formatear_mensaje(resultado) if isinstance(resultado, dict) else resultado
    await update.message.reply_text(mensaje, parse_mode='Markdown')

# ℹ️ Botón "Info"
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "🧠 *Eye of God* evalúa el riesgo de BTC según su volatilidad.\n"
        "Cuanto mayor es la volatilidad, mayor es el riesgo.\n"
        "🧮 Fórmula usada: `riesgo = |Δprecio| / precio_inicial`"
    )
    await update.message.reply_text(mensaje, parse_mode='Markdown')

# ⛔ Botón "Parar"
async def parar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 Alertas automáticas detenidas (modo básico).")

# 🎛️ Manejador de botones
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
            "🧮 Fórmula usada: `riesgo = |Δprecio| / precio_inicial`",
            parse_mode='Markdown',
        )

    elif data == "parar":
        await query.edit_message_text("🛑 Alertas automáticas desactivadas (modo básico).")

# 🧯 Manejador de errores
async def manejar_errores(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f"⚠️ Error manejado: {context.error}")
    if update and hasattr(update, "message"):
        await update.message.reply_text("❌ Algo salió mal, pero estoy trabajando en ello.")

# ▶️ Función principal
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("riesgo", riesgo))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("parar", parar))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(manejar_errores)

    print("🚀 Eye of God corriendo en Telegram...")
    app.run_polling()

# 🏁 Ejecutar
if __name__ == "__main__":
    main()
