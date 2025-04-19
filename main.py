import logging
import asyncio
import aiohttp
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta

TOKEN = "6696093539:AAGY4X7KiIrtsGnZlhGcGkpStOG5fEwBDrk"
UMBRAL_VARIACION = 0.012
UMBRAL_ACELERACION = 0.007

MONEDAS = {
    "bitcoin": "BTC",
    "binancecoin": "BNB",
    "solana": "SOL",
    "cardano": "ADA",
    "ripple": "XRP"
}

precios_historicos = {m: [] for m in MONEDAS}
alertas_recientes = {}
usuarios_activos = set()

# 🧠 Obtener precios desde CoinGecko
async def obtener_precios():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ",".join(MONEDAS), "vs_currencies": "usd"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            return await resp.json()

def calcular_variacion(pasado, actual):
    return (actual - pasado) / pasado

def detectar_aceleracion(precios):
    if len(precios) < 4:
        return False
    p1, p2, p3, p4 = [x[1] for x in precios[-4:]]
    v1 = calcular_variacion(p1, p2)
    v2 = calcular_variacion(p2, p3)
    v3 = calcular_variacion(p3, p4)

    if abs(v1) > UMBRAL_ACELERACION and abs(v2) > UMBRAL_ACELERACION and abs(v3) > UMBRAL_ACELERACION:
        if (v1 > 0 and v2 > 0 and v3 > 0) or (v1 < 0 and v2 < 0 and v3 < 0):
            return True
    return False

# 🚀 Enviar alerta a todos los usuarios activos
async def enviar_alerta(app, moneda, tipo, variacion, actual):
    nombre = MONEDAS[moneda]
    emoji = "🟢" if tipo == "subida" else "🔴"
    tipo_alerta = "ACELERACIÓN ALCISTA" if tipo == "subida" else "ACELERACIÓN BAJISTA"
    mensaje = (
        f"🧿 *Ojo de Dios Detecta Movimiento Potencial*\n\n"
        f"{emoji} *{tipo_alerta} en {nombre}*\n"
        f"💰 Precio actual: ${actual:.2f}\n"
        f"📈 Cambio acelerado: {round(variacion * 100, 2)}%\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
    )
    for chat_id in usuarios_activos:
        await app.bot.send_message(chat_id=chat_id, text=mensaje, parse_mode="Markdown")

# 🟢 Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    usuarios_activos.add(chat_id)
    await update.message.reply_text("👁️ Ojo de Dios activado. Te notificaré movimientos importantes.")

# 🔁 Bucle de monitoreo
async def monitorear(app):
    while True:
        datos = await obtener_precios()
        for clave in MONEDAS:
            precio = datos[clave]["usd"]
            precios_historicos[clave].append((datetime.now(), precio))
            precios_historicos[clave] = precios_historicos[clave][-6:]

            if len(precios_historicos[clave]) >= 4:
                viejo_precio = precios_historicos[clave][-4][1]
                variacion = calcular_variacion(viejo_precio, precio)
                if abs(variacion) >= UMBRAL_VARIACION:
                    ultima = alertas_recientes.get(clave)
                    if not ultima or datetime.now() - ultima > timedelta(minutes=10):
                        tipo = "subida" if variacion > 0 else "bajada"
                        await enviar_alerta(app, clave, tipo, variacion, precio)
                        alertas_recientes[clave] = datetime.now()

            if detectar_aceleracion(precios_historicos[clave]):
                ultima = alertas_recientes.get(f"{clave}_aceleracion")
                if not ultima or datetime.now() - ultima > timedelta(minutes=10):
                    tendencia = calcular_variacion(
                        precios_historicos[clave][-2][1],
                        precios_historicos[clave][-1][1]
                    )
                    tipo = "subida" if tendencia > 0 else "bajada"
                    await enviar_alerta(app, clave, tipo, tendencia, precio)
                    alertas_recientes[f"{clave}_aceleracion"] = datetime.now()

        await asyncio.sleep(60)

# 🧠 Lanzar bot y monitoreo
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    asyncio.create_task(monitorear(app))
    await app.run_polling()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
