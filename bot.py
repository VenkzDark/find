import os
import io
import socket
import asyncio
import aiohttp
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# Si quieres que CUALQUIERA pueda usar el bot sin pedir permiso, cambia False a True:
MODO_PUBLICO = True

admins = {OWNER_ID}
usuarios_autorizados = {OWNER_ID}

def tiene_acceso(uid: int) -> bool:
    if MODO_PUBLICO:
        return True
    return uid in usuarios_autorizados

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not tiene_acceso(uid):
        await update.message.reply_text(
            f"🔒 **Bot Privado**\nTu ID `{uid}` requiere aprobación del Owner.",
            parse_mode="Markdown"
        )
        if OWNER_ID != 0:
            try:
                await context.bot.send_message(
                    chat_id=OWNER_ID,
                    text=f"📩 Solicitud de acceso de `{uid}` (@{update.effective_user.username or 'Sin alias'})\n👉 `/aceptar {uid}`",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        return

    texto = (
        "🛰️ **OSINT & INFO STUDIO • BOT** 🛰️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "• `/ip 8.8.8.8` — Geolocalización, ISP y detección de VPN/Hosting\n"
        "• `/dns google.com` — Ver registros DNS e IPs de un dominio\n"
        "• `/url https://bit.ly...` — Descubrir el destino real de un link\n"
        "• `/qr texto o link` — Generar código QR al instante\n"
        "• `/cripto bitcoin` — Precio en vivo de cualquier criptomoneda\n"
    )
    if uid in admins:
        texto += (
            "\n🛡️ **Panel Admin:**\n"
            "• `/aceptar ID` | `/denegar ID` | `/addadmin ID`"
        )
    await update.message.reply_text(texto, parse_mode="Markdown")

async def cmd_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tiene_acceso(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("ℹ️ Uso: `/ip 8.8.8.8` o `/ip google.com`", parse_mode="Markdown")
        return

    objetivo = context.args.strip().replace("https://", "").replace("http://", "").split("/")
    url = f"http://ip-api.com{objetivo}?fields=status,message,country,regionName,city,isp,org,as,proxy,hosting,query"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=8) as resp:
                data = await resp.json()

        if data.get("status") != "success":
            await update.message.reply_text(f"❌ No se pudo consultar: `{data.get('message', 'IP inválida')}`", parse_mode="Markdown")
            return

        es_vpn = "Sí (Proxy/VPN)" if data.get("proxy") else "No detectado"
        es_host = "Sí (Servidor/Datacenter)" if data.get("hosting") else "Residencial / Móvil"

        texto = (
            f"🌐 **REPORTE IP / DOMINIO**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• **IP resuelta:** `{data.get('query')}`\n"
            f"• **Ubicación:** {data.get('city')}, {data.get('regionName')}, {data.get('country')}\n"
            f"• **Proveedor (ISP):** `{data.get('isp')}`\n"
            f"• **Organización:** `{data.get('org')}`\n"
            f"• **ASN:** `{data.get('as')}`\n"
            f"• **Proxy / VPN:** {es_vpn}\n"
            f"• **Tipo de red:** {es_host}"
        )
        await update.message.reply_text(texto, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al consultar IP: `{str(e)[:50]}`", parse_mode="Markdown")

async def cmd_dns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tiene_acceso(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("ℹ️ Uso: `/dns github.com`", parse_mode="Markdown")
        return

    dominio = context.args.strip().lower().replace("https://", "").replace("http://", "").split("/")
    tipos = ["A", "AAAA", "MX", "NS", "TXT"]
    resultados = []

    try:
        async with aiohttp.ClientSession() as session:
            for tipo in tipos:
                api_url = f"https://dns.google{dominio}&type={tipo}"
                async with session.get(api_url, timeout=6) as resp:
                    data = await resp.json()
                    ans = data.get("Answer", [])
                    if ans:
                        valores = ", ".join([a.get("data", "") for a in ans[:3]])
                        resultados.append(f"• **{tipo}:** `{valores}`")

        if not resultados:
            await update.message.reply_text(f"❌ No se encontraron registros DNS para `{dominio}`.", parse_mode="Markdown")
            return

        cuerpo = "\n".join(resultados)
        await update.message.reply_text(
            f"🔍 **REGISTROS DNS • {dominio}**\n━━━━━━━━━━━━━━━━━━━━\n{cuerpo}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error DNS: `{str(e)[:50]}`", parse_mode="Markdown")
        
    dominio = context.args.strip().lower().replace("https://", "").replace("http://", "").split("/")
    tipos = ["A", "AAAA", "MX", "NS", "TXT"]
    resultados = []

    try:
        async with aiohttp.ClientSession() as session:
            for tipo in tipos:
                api_url = f"https://dns.google{dominio}&type={tipo}"
                async with session.get(api_url, timeout=6) as resp:
                    data = await resp.json()
                    ans = data.get("Answer", [])
                    if ans:
                        valores = ", ".join([a.get("data", "") for a in ans[:3]])
                        resultados.append(f"• **{tipo}:** `{valores}`")

        if not resultados:
            await update.message.reply_text(f"❌ No se encontraron registros DNS para `{dominio}`.", parse_mode="Markdown")
            return

        cuerpo = "\n".join(resultados)
        await update.message.reply_text(
            f"🔍 **REGISTROS DNS • {dominio}**\n━━━━━━━━━━━━━━━━━━━━\n{cuerpo}",
            parse_mode="Markdown"
        )
        except Exception as e:
        await update.message.reply_text(f"⚠️ Error DNS: `{str(e)[:50]}`", parse_mode="Markdown")


  async def cmd_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
      if not tiene_acceso(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("ℹ️ Uso: `/url https://bit.ly`", parse_mode="Markdown")
        return

    enlace = context.args.strip()
    if not enlace.startswith("http"):
        enlace = "https://" + enlace

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(enlace, allow_redirects=True, timeout=10) as resp:
                destino_final = str(resp.url)
                historial = [str(h.url) for h in resp.history]

        saltos = f"\n• **Redirecciones ({len(historial)}):** " + " ➡️ ".join([f"`{u}`" for u in historial]) if historial else ""
        texto = (
            f"🔗 **RASTREO DE ENLACE**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• **Original:** `{enlace}`\n"
            f"• **Destino Real:** `{destino_final}`\n"
            f"• **Estado HTTP:** `{resp.status}`{saltos}"
        )
        await update.message.reply_text(texto, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"⚠️ No se pudo rastrear el enlace: `{str(e)[:50]}`", parse_mode="Markdown")

async def cmd_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tiene_acceso(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("ℹ️ Uso: `/qr https://t.me`", parse_mode="Markdown")
        return

    contenido = " ".join(context.args)
    api_qr = f"https://qrserver.com{aiohttp.helpers.quote(contenido)}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_qr, timeout=10) as resp:
                img_bytes = await resp.read()

        archivo = io.BytesIO(img_bytes)
        archivo.name = "codigo_qr.png"
        await update.message.reply_photo(
            photo=archivo,
            caption=f"📱 **QR generado para:** `{contenido[:60]}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error generando QR: `{str(e)[:50]}`", parse_mode="Markdown")

async def cmd_cripto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tiene_acceso(update.effective_user.id):
        return
    moneda = context.args.lower().strip() if context.args else "bitcoin"
    alias = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana", "ton": "the-open-network", "ltc": "litecoin", "doge": "dogecoin"}
    moneda_id = alias.get(moneda, moneda)

    url = f"https://coingecko.com{moneda_id}&vs_currencies=usd,mxn,eur&include_24hr_change=true"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=8) as resp:
                data = await resp.json()

        if moneda_id not in data:
            await update.message.reply_text(f"❌ Moneda `{moneda}` no encontrada. Prueba con `bitcoin`, `solana`, `ton`, `ethereum`.", parse_mode="Markdown")
            return

        info = data[moneda_id]
        cambio = info.get("usd_24h_change", 0)
        icono = "📈" if cambio >= 0 else "📉"

        texto = (
            f"💰 **PRECIO EN VIVO • {moneda_id.upper()}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• **USD:** `${info.get('usd'):,.2f}`\n"
            f"• **MXN:** `${info.get('mxn'):,.2f}`\n"
            f"• **EUR:** `€{info.get('eur'):,.2f}`\n"
            f"• **Cambio 24h:** {icono} `{cambio:+.2f}%`"
        )
        await update.message.reply_text(texto, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error consultando precio: `{str(e)[:50]}`", parse_mode="Markdown")

async def cmd_aceptar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID or not context.args or not context.args.isdigit():
        return
    uid = int(context.args)
    usuarios_autorizados.add(uid)
    await update.message.reply_text(f"✅ Usuario `{uid}` aceptado.", parse_mode="Markdown")

async def cmd_denegar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID or not context.args or not context.args.isdigit():
        return
    uid = int(context.args)
    if uid != OWNER_ID:
        usuarios_autorizados.discard(uid)
        admins.discard(uid)
        await update.message.reply_text(f"🚫 Acceso revocado a `{uid}`.", parse_mode="Markdown")

async def cmd_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID or not context.args or not context.args.isdigit():
        return
    uid = int(context.args)
    usuarios_autorizados.add(uid)
    admins.add(uid)
    await update.message.reply_text(f"🛡️ Admin agregado: `{uid}`.", parse_mode="Markdown")

async def web_ping(request):
    return web.Response(text="OSINT Studio Bot activo")

async def iniciar_todo():
    web_app = web.Application()
    web_app.router.add_get("/", web_ping)
    runner = web.AppRunner(web_app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ip", cmd_ip))
    app.add_handler(CommandHandler("dns", cmd_dns))
    app.add_handler(CommandHandler("url", cmd_url))
    app.add_handler(CommandHandler("qr", cmd_qr))
    app.add_handler(CommandHandler("cripto", cmd_cripto))
    app.add_handler(CommandHandler("aceptar", cmd_aceptar))
    app.add_handler(CommandHandler("denegar", cmd_denegar))
    app.add_handler(CommandHandler("addadmin", cmd_addadmin))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print(f"Bot OSINT activo en puerto {port}...")
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(iniciar_todo())
  
