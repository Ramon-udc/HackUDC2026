import logging
import requests
import io
import warnings
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# 1. Configuración de arranque (Evita bloqueos y limpia consola)
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.ERROR)

# ---------------- CONFIGURACIÓN ----------------
TOKEN_TELEGRAM = "8736047897:AAGQGwk6vYb-JDrAftJtjNjXH7X3vuIkU8g"
TOKEN_METEOGALICIA = "O7d8a21OKeGZ20z9xN5YyMK4JM3U42sUq6MCpy8Jo90H9l3Y8We42Bpk8SMp5O9z"
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

# ---------------- LÓGICA BIOLÓGICA ANUAL ----------------

def predecir_capturas(viento, zona):
    """Matriz biológica dinámica según mes y ubicación."""
    mes = datetime.now().month
    especies = []
    prob = "Alta" if viento < 15 else "Media-Baja"

    if mes in [1, 2, 3]: # Invierno
        especies.append("🐟 *Lubina*: Activa con viento.")
        especies.append("🐠 *Sargo*: Época de rompientes.")
        if zona == "sur" and viento < 12: especies.append("🦑 *Choco*: Entrando en rías.")
    elif mes in [4, 5, 6]: # Primavera
        especies.append("🐟 *Xarda/Caballa*: Gran actividad.")
        especies.append("🐟 *Jurel*: Bancos acercándose.")
        especies.append("🐠 *Dorada*: Primeras capturas en las Rías Baixas.")
    elif mes in [7, 8, 9]: # Verano
        especies.append("🦑 *Chipirón*: Noches en el muelle.")
        especies.append("🐟 *Agulla*: Actividad en superficie.")
    else: # Otoño
        especies.append("🦑 *Calamar*: Temporada fuerte.")
        especies.append("🐟 *Faneca*: Fondos arenosos.")

    return prob, "\n".join(especies)

# ---------------- EXTRACCIÓN DE DATOS ----------------

def obtener_viento_meteo(id_puerto):
    """Consulta técnica a MeteoGalicia para predicción."""
    url = f"https://servizos.meteogalicia.gal/apiv5/getNumericForecastInfo?locationIds={id_puerto}&API_KEY={TOKEN_METEOGALICIA}&format=application/json"
    objetivo = (datetime.now() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
    target_str = objetivo.strftime('%Y-%m-%dT%H:%M')
    try:
        r = requests.get(url, timeout=12)
        if r.status_code == 200:
            js = r.json()
            days = js['features'][0]['properties']['days']
            for day in days:
                for v in day.get('variables', []):
                    if v.get('name', '').lower() == 'wind':
                        for item in v.get('values', []):
                            if target_str in item.get('timeInstant', ''):
                                return float(item.get('moduleValue', 0))
        return 0.0
    except: return 0.0

# ---------------- HANDLERS TELEGRAM ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btns = [[InlineKeyboardButton(n, callback_data=f"puerto|{n}")] for n in PUERTOS]
    await update.message.reply_text("🎣 *PeixeGalicia*\nPredicción 24h + Gráficos reales.\nSelecciona puerto:", 
                                   reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tipo, valor = query.data.split("|")

    if tipo == "puerto":
        context.user_data["puerto"] = valor
        btns = [
            [InlineKeyboardButton("🔍 Predicción de pesca", callback_data="pesca|analisis")],
            [InlineKeyboardButton("🌊 Olas", callback_data="grafico|olas"), 
             InlineKeyboardButton("💨 Viento", callback_data="grafico|viento")],
            [InlineKeyboardButton("🌡️ Temperatura", callback_data="grafico|temp")],
            [InlineKeyboardButton("🏠 Cambiar Puerto", callback_data="volver|puertos")]
        ]
        await query.edit_message_text(f"📍 Puerto: *{valor}*", reply_markup=InlineKeyboardMarkup(btns), parse_mode="Markdown")

    elif tipo == "pesca":
        p_nombre = context.user_data.get("puerto")
        info = PUERTOS[p_nombre]
        msg = await query.message.reply_text(f"⏳ Analizando condiciones...")
        viento = obtener_viento_meteo(info['id'])
        prob, lista = predecir_capturas(viento, info['zona'])
        
        texto = (f"📋 *INFORME: {p_nombre.upper()}*\n💨 Viento: {viento} km/h\n"
                 f"📈 *Éxito:* {prob}\n\n✅ *Especies probables:*\n{lista}")
        await msg.edit_text(texto, parse_mode="Markdown")

    elif tipo == "grafico":
        p_nombre = context.user_data.get("puerto")
        p_id = PUERTOS[p_nombre]["id"]
        panel_id = PANELES[valor]
        url = f"{GRAFANA_URL}/render/d-solo/{DASHBOARD_UID}/peixealert?orgId=1&panelId={panel_id}&var-puerto={p_id}&width=1000&height=500"
        
        msg_g = await query.message.reply_text(f"⏳ Cargando gráfica de {valor}...")
        try:
            r = requests.get(url, headers={"Authorization": f"Bearer {API_KEY_GRAFANA}"}, timeout=25)
            if r.status_code == 200:
                await msg_g.delete()
                await query.message.reply_photo(photo=io.BytesIO(r.content), caption=f"📊 {valor.capitalize()} en {p_nombre}")
            else:
                await msg_g.edit_text("❌ Error al conectar con Grafana.")
        except:
            await msg_g.edit_text("❌ Tiempo de espera agotado.")

    elif tipo == "volver":
        btns = [[InlineKeyboardButton(n, callback_data=f"puerto|{n}")] for n in PUERTOS]
        await query.message.reply_text("📍 Selecciona puerto:", reply_markup=InlineKeyboardMarkup(btns))

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("PeixeGalicia ONLINE")
    app.run_polling(drop_pending_updates=True)