import logging
import requests
import io
import warnings
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Desactivar advertencias de seguridad para agilizar el arranque en redes locales
warnings.filterwarnings("ignore", category=UserWarning)

# ---------------- CONFIG ----------------
TOKEN_TELEGRAM = "8736047897:AAGQGwk6vYb-JDrAftJtjNjXH7X3vuIkU8g"
GRAFANA_URL = "https://maytecarballo.grafana.net"
API_KEY_GRAFANA = "glsa_WLhnhkhHJvcBCnF4i77fD2RSRDI47vPl_5eee0872"
DASHBOARD_UID = "mac9q76"

PUERTOS = {
    "Marín":      {"id": "1000091", "zona": "sur"},
    "Vigo":       {"id": "1000259", "zona": "sur"},
    "Coruña":     {"id": "1002284", "zona": "norte"},
    "Vilagarcía": {"id": "1001597", "zona": "sur"},
    "Ferrol":     {"id": "1002284", "zona": "norte"},
}

PANELES = {"olas": 3, "viento": 4, "temp": 7}

# ---------------- LÓGICA DE EXTRACCIÓN GRAFANA ----------------

def obtener_valor_grafana(panel_id, puerto_id):
    """Extrae el último valor real de Grafana evitando el valor 0."""
    url = f"{GRAFANA_URL}/api/ds/query"
    headers = {
        "Authorization": f"Bearer {API_KEY_GRAFANA}",
        "Content-Type": "application/json"
    }

    # Consulta optimizada para el datasource JSON
    payload = {
        "queries": [
            {
                "refId": "A",
                "datasource": {"type": "marcusolsson-json-datasource"},
                "intervalMs": 60000,
                "maxDataPoints": 100
            }
        ],
        "range": {"from": "now-1h", "to": "now"}
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Navegamos por los resultados de Grafana
            frames = data.get("results", {}).get("A", {}).get("frames", [])
            if frames:
                # Los valores numéricos suelen estar en la segunda columna (índice 1)
                values = frames[0].get("data", {}).get("values", [])
                if len(values) >= 2:
                    # Filtramos Nones y ceros iniciales para buscar el dato real
                    serie_datos = [float(v) for v in values[1] if v is not None]
                    if serie_datos:
                        return round(serie_datos[-1], 2)
        return 0.0
    except Exception:
        return 0.0

# ---------------- HANDLERS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btns = [[InlineKeyboardButton(n, callback_data=f"puerto|{n}")] for n in PUERTOS]
    await update.message.reply_text("🌊 *PeixeAlert* conectado.\nElige puerto:", 
                                   reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if "|" not in query.data: return
    tipo, valor = query.data.split("|")

    if tipo == "puerto":
        context.user_data["puerto"] = valor
        btns = [
            [InlineKeyboardButton("🎣 ANÁLISIS DE PESCA", callback_data="pesca|analisis")],
            [InlineKeyboardButton("🌊 Olas", callback_data="grafico|olas"), 
             InlineKeyboardButton("💨 Vento", callback_data="grafico|viento")],
            [InlineKeyboardButton("🌡️ Temp", callback_data="grafico|temp")],
            [InlineKeyboardButton("🏠 Cambiar Puerto", callback_data="volver|puertos")]
        ]
        await query.edit_message_text(f"📍 Puerto: *{valor}*", reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

    elif tipo == "pesca":
        p_nombre = context.user_data.get("puerto")
        if not p_nombre: return
        
        p_id = PUERTOS[p_nombre]["id"]
        await query.message.reply_text(f"⏳ Extrayendo datos reales de Grafana...")

        # Obtener valores de los paneles
        ola = obtener_valor_grafana(PANELES["olas"], p_id)
        viento = obtener_valor_grafana(PANELES["viento"], p_id)
        temp = obtener_valor_grafana(PANELES["temp"], p_id)

        peces = "🌊 *Lubina*" if ola > 1.5 else "⚓ *Calamar*" if ola < 0.6 else "🐟 *Sargo*"
        
        texto = (f"🎣 *INFORME: {p_nombre.upper()}*\n"
                 f"━━━━━━━━━━━━━━\n"
                 f"🌊 *Ola:* {ola}m\n"
                 f"💨 *Vento:* {viento}km/h\n"
                 f"🌡️ *Agua:* {temp}ºC\n\n"
                 f"✅ *Especies sugeridas:* \n{peces}")
        await query.message.reply_text(texto, parse_mode="Markdown")

    elif tipo == "grafico":
        p_id = PUERTOS[context.user_data.get("puerto")]["id"]
        panel_id = PANELES[valor]
        render_url = f"{GRAFANA_URL}/render/d-solo/{DASHBOARD_UID}/peixealert?orgId=1&panelId={panel_id}&var-puerto={p_id}&width=1000&height=500"
        
        msg = await query.message.reply_text("⏳ Cargando...")
        try:
            r = requests.get(render_url, headers={"Authorization": f"Bearer {API_KEY_GRAFANA}"}, timeout=25)
            if r.status_code == 200:
                await msg.delete()
                await query.message.reply_photo(photo=io.BytesIO(r.content), caption=f"📊 Gráfico de {valor}")
            else:
                await msg.edit_text(f"❌ Error Grafana: {r.status_code}")
        except:
            await msg.edit_text("❌ Tiempo agotado.")

    elif tipo == "volver":
        btns = [[InlineKeyboardButton(n, callback_data=f"puerto|{n}")] for n in PUERTOS]
        await query.message.reply_text("📍 Selecciona puerto:", reply_markup=InlineKeyboardMarkup(btns))

# ---------------- MAIN ----------------
if __name__ == "__main__":
    # Iniciar aplicación ignorando actualizaciones antiguas para evitar KeyboardInterrupt
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 PeixeAlert ONLINE. (Extrayendo de Grafana Cloud)")
    app.run_polling(drop_pending_updates=True)