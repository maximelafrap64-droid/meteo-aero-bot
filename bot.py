import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import requests
from datetime import datetime

# Configuration du logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Token du bot (à remplacer par votre token)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'VOTRE_TOKEN_ICI')

# Fonction pour récupérer le METAR depuis Aeroweb
def get_metar(icao_code):
    try:
        url = f"https://aviation.meteo.fr/FR/aviation/SAT.php?icao={icao_code}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Simplification - dans la vraie version, parser le HTML
            return f"METAR pour {icao_code}:\n(Voir: {url})"
        return f"Impossible de récupérer le METAR pour {icao_code}"
    except Exception as e:
        return f"Erreur: {str(e)}"

# Fonction pour récupérer le TAF depuis Aeroweb
def get_taf(icao_code):
    try:
        url = f"https://aviation.meteo.fr/FR/aviation/SAT.php?icao={icao_code}"
        return f"TAF pour {icao_code}:\n(Voir: {url})"
    except Exception as e:
        return f"Erreur: {str(e)}"

# Fonction pour récupérer les NOTAM depuis SofiaBriefing
def get_notam(icao_code, date_vol):
    try:
        # Sofia Briefing URL
        url = f"https://www.sofia-briefing.com/notam/{icao_code}"
        return f"NOTAMs pour {icao_code} le {date_vol}:\n{url}"
    except Exception as e:
        return f"Erreur: {str(e)}"

# Fonction pour générer un lien Windy
def get_windy_link(lat, lon):
    return f"https://www.windy.com/?{lat},{lon},8"

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = """
✈️ *Bienvenue sur votre Assistant Météo Aéronautique* ✈️

Je peux vous fournir :
• METAR & TAF (Aeroweb Météo-France)
• TEMSI & WINTEM
• NOTAMs (SofiaBriefing)
• Radar météo (Windy)

*Commandes disponibles :*
/vol_local - Vol local depuis un terrain
/trajet - Vol entre deux points (A → B)
/metar ICAO - METAR d'un terrain
/taf ICAO - TAF d'un terrain
/notam ICAO DATE - NOTAMs (ex: /notam LFPG 2025-01-20)
/help - Aide

Type de vol : VFR ou IFR ?
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

# Commande /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
*Guide d'utilisation* 📖

*Vol local :*
`/vol_local LFPG VFR 2025-01-20`
Donne METAR, TAF, NOTAM et radar pour un vol local

*Trajet A→B :*
`/trajet LFPG LFPO VFR 2025-01-20`
Donne les infos météo pour le départ, l'arrivée et le trajet

*Commandes rapides :*
`/metar LFPG` - METAR uniquement
`/taf LFPG` - TAF uniquement
`/notam LFPG 2025-01-20` - NOTAMs

*Format :*
• Code OACI : 4 lettres (ex: LFPG)
• Type vol : VFR ou IFR
• Date : AAAA-MM-JJ
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Commande /metar
async def metar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /metar ICAO (ex: /metar LFPG)")
        return
    
    icao = context.args[0].upper()
    metar = get_metar(icao)
    await update.message.reply_text(metar)

# Commande /taf
async def taf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /taf ICAO (ex: /taf LFPG)")
        return
    
    icao = context.args[0].upper()
    taf = get_taf(icao)
    await update.message.reply_text(taf)

# Commande /notam
async def notam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /notam ICAO DATE (ex: /notam LFPG 2025-01-20)")
        return
    
    icao = context.args[0].upper()
    date_vol = context.args[1]
    notam = get_notam(icao, date_vol)
    await update.message.reply_text(notam)

# Commande /vol_local
async def vol_local(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /vol_local ICAO VFR/IFR DATE\nEx: /vol_local LFPG VFR 2025-01-20")
        return
    
    icao = context.args[0].upper()
    flight_type = context.args[1].upper()
    date_vol = context.args[2]
    
    response = f"🛩️ *Vol Local depuis {icao}*\n"
    response += f"Type: {flight_type} | Date: {date_vol}\n\n"
    
    response += f"*METAR:*\n{get_metar(icao)}\n\n"
    response += f"*TAF:*\n{get_taf(icao)}\n\n"
    response += f"*NOTAMs:*\n{get_notam(icao, date_vol)}\n\n"
    response += f"*Radar Windy:*\n{get_windy_link(48.7, 2.3)}\n\n"
    
    if flight_type == 'VFR':
        response += "📋 *Docs VFR:* TEMSI, WINTEM disponibles sur Aeroweb"
    else:
        response += "📋 *Docs IFR:* Cartes TEMSI, WINTEM, cartes en route"
    
    await update.message.reply_text(response, parse_mode='Markdown')

# Commande /trajet
async def trajet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 4:
        await update.message.reply_text("Usage: /trajet ICAO_A ICAO_B VFR/IFR DATE\nEx: /trajet LFPG LFPO VFR 2025-01-20")
        return
    
    icao_a = context.args[0].upper()
    icao_b = context.args[1].upper()
    flight_type = context.args[2].upper()
    date_vol = context.args[3]
    
    response = f"✈️ *Trajet {icao_a} → {icao_b}*\n"
    response += f"Type: {flight_type} | Date: {date_vol}\n\n"
    
    response += f"*DÉPART - {icao_a}:*\n"
    response += f"METAR: {get_metar(icao_a)}\n"
    response += f"TAF: {get_taf(icao_a)}\n"
    response += f"NOTAMs: {get_notam(icao_a, date_vol)}\n\n"
    
    response += f"*ARRIVÉE - {icao_b}:*\n"
    response += f"METAR: {get_metar(icao_b)}\n"
    response += f"TAF: {get_taf(icao_b)}\n"
    response += f"NOTAMs: {get_notam(icao_b, date_vol)}\n\n"
    
    response += f"*Route & Météo:*\n"
    response += f"Radar: {get_windy_link(48.7, 2.3)}\n"
    response += "TEMSI/WINTEM: https://aviation.meteo.fr\n"
    
    await update.message.reply_text(response, parse_mode='Markdown')

# Gestion des erreurs
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

# Fonction principale
def main():
    # Créer l'application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Ajouter les handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("metar", metar_command))
    application.add_handler(CommandHandler("taf", taf_command))
    application.add_handler(CommandHandler("notam", notam_command))
    application.add_handler(CommandHandler("vol_local", vol_local))
    application.add_handler(CommandHandler("trajet", trajet))
    
    # Gestion des erreurs
    application.add_error_handler(error_handler)
    
    # Démarrer le bot
    logger.info("Bot démarré!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
