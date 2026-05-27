STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # Language selection
        "choose_language":   "Choose your language / Elige tu idioma:",
        "language_set":      "🇬🇧 Language set to English.",
        "language_set_new":  "🇬🇧 Language set to English.\n\nRun /setup to connect your Gmail and get started.",
        "setup_in_progress": "Please complete setup first, then use /language to change your language.",

        # /start — welcome back (active user)
        "welcome_back": (
            "Welcome back, {name}! Your Gmail digest is active.\n\n"
            "Use /status to see your settings or /digest to check your inbox now.\n\n"
            "Commands:\n"
            "/setup — connect Gmail and configure filters\n"
            "/status — view your settings\n"
            "/digest — check inbox now\n"
            "/ping — check if bot is alive\n"
            "/help  — ask a question about MailPilot\n"
            "/reset — clear /help conversation history\n"
            "/language — cambiar idioma / change language\n\n"
            "📬 Monitoring your inbox every 15 minutes for urgent emails."
        ),

        # Setup wizard
        "setup_step1": (
            "Let's get you set up! (Step 1 of 3)\n\n"
            "Please send the Gmail address you want to monitor."
        ),
        "setup_step1_invalid": (
            "That doesn't look like a Gmail address.\n"
            "Please try again (e.g. yourname@gmail.com)."
        ),
        "setup_step2": (
            "Step 2 of 3\n\n"
            "Enter the keywords I should look for, separated by commas.\n"
            "Example: Python, backend, remote, senior"
        ),
        "setup_step2_empty":         "Please enter at least one keyword (e.g. Python).",
        "setup_step3": (
            "Step 3 of 3\n\n"
            "What time should I send your daily digest? (UTC)\n"
            "Format: HH:MM — e.g. 09:00"
        ),
        "setup_step3_invalid_format": "Please use HH:MM format (e.g. 09:00).",
        "setup_step3_invalid_range":  "Invalid time — hours must be 00–23 and minutes 00–59 (e.g. 09:00).",
        "setup_complete": (
            "Setup complete! I'll check your Gmail every day and send important "
            "emails at {time} UTC.\n\n"
            "Use /status to review your settings or /digest to trigger a digest right now."
        ),

        # /ping
        "ping": "🟢 I'm alive and monitoring your inbox.",

        # /status
        "setup_required": "Setup required. Run /setup first.",
        "status_body": (
            "MailPilot Status\n\n"
            "Gmail: {gmail}\n"
            "Keywords: {keywords}\n"
            "Daily digest: {time} UTC\n\n"
            "Last 24 h: {total} emails received, {important} marked important\n\n"
            "Use /digest to get your current digest now."
        ),

        # /digest
        "checking_inbox":   "⏳ Checking your inbox...",
        "gmail_auth_error": "❌ Could not connect to Gmail. Please run /setup again.",
        "fetch_error":      "❌ Could not fetch emails. Try /setup to reconnect.",
        "no_emails":        "📭 No new important emails.",
        "digest_sent":      "Digest sent — {total} important email(s).",

        # Background jobs
        "gmail_expired":   "Your Gmail authorization has expired. Run /setup to reconnect.",
        "reconnect_error": "❌ Please run /setup to reconnect.",

        # Alert & digest email messages
        "alert_header":   "⚠️ Urgent email",
        "from_label":     "From",
        "subject_label":  "Subject",
        "score_label":    "Score",
        "digest_title":   "MailPilot Digest — {count} important email(s)",

        # /help
        "help_no_question": (
            "Ask me anything about MailPilot!\n"
            "Example: /help how do keywords work?"
        ),
        "help_ai_error": (
            "I couldn't answer that right now. "
            "Try /setup to check your settings or contact support."
        ),

        # /reset
        "history_cleared": "Conversation history cleared.",

        # Fallback
        "unknown_command": (
            "Sorry, I didn't understand that.\n\n"
            "Available commands:\n"
            "/start  — restart the bot\n"
            "/setup  — connect Gmail and configure filters\n"
            "/status — view your settings and last 24 h stats\n"
            "/digest — get today's important emails now\n"
            "/ping   — check the bot is running\n"
            "/help   — ask a question about MailPilot\n"
            "/reset  — clear /help conversation history\n"
            "/language — cambiar idioma / change language"
        ),
    },

    "es": {
        # Language selection
        "choose_language":   "Elige tu idioma / Choose your language:",
        "language_set":      "🇪🇸 Idioma cambiado a Español.",
        "language_set_new":  "🇪🇸 Idioma configurado en Español.\n\nEjecuta /setup para conectar tu Gmail y comenzar.",
        "setup_in_progress": "Por favor completa la configuración primero, luego usa /language para cambiar tu idioma.",

        # /start — welcome back (active user)
        "welcome_back": (
            "¡Bienvenido de nuevo, {name}! Tu resumen de Gmail está activo.\n\n"
            "Usa /status para ver tu configuración o /digest para revisar tu bandeja ahora.\n\n"
            "Comandos:\n"
            "/setup — conectar Gmail y configurar filtros\n"
            "/status — ver tu configuración\n"
            "/digest — revisar bandeja ahora\n"
            "/ping — verificar que el bot está activo\n"
            "/help  — hacer una pregunta sobre MailPilot\n"
            "/reset — limpiar historial de /help\n"
            "/language — cambiar idioma / change language\n\n"
            "📬 Monitoreando tu bandeja cada 15 minutos en busca de correos urgentes."
        ),

        # Setup wizard
        "setup_step1": (
            "¡Vamos a configurar tu cuenta! (Paso 1 de 3)\n\n"
            "Envía la dirección de Gmail que deseas monitorear."
        ),
        "setup_step1_invalid": (
            "Eso no parece una dirección de Gmail.\n"
            "Intenta de nuevo (ej. tunombre@gmail.com)."
        ),
        "setup_step2": (
            "Paso 2 de 3\n\n"
            "Ingresa las palabras clave que debo buscar, separadas por comas.\n"
            "Ejemplo: Python, backend, remoto, senior"
        ),
        "setup_step2_empty":         "Por favor ingresa al menos una palabra clave (ej. Python).",
        "setup_step3": (
            "Paso 3 de 3\n\n"
            "¿A qué hora debo enviarte el resumen diario? (UTC)\n"
            "Formato: HH:MM — ej. 09:00"
        ),
        "setup_step3_invalid_format": "Por favor usa el formato HH:MM (ej. 09:00).",
        "setup_step3_invalid_range":  "Hora inválida — las horas deben ser 00–23 y los minutos 00–59 (ej. 09:00).",
        "setup_complete": (
            "¡Configuración completa! Revisaré tu Gmail todos los días y enviaré "
            "correos importantes a las {time} UTC.\n\n"
            "Usa /status para revisar tu configuración o /digest para obtener un resumen ahora."
        ),

        # /ping
        "ping": "🟢 Estoy activo y monitoreando tu bandeja.",

        # /status
        "setup_required": "Configuración requerida. Ejecuta /setup primero.",
        "status_body": (
            "Estado de MailPilot\n\n"
            "Gmail: {gmail}\n"
            "Palabras clave: {keywords}\n"
            "Resumen diario: {time} UTC\n\n"
            "Últimas 24 h: {total} correos recibidos, {important} marcados como importantes\n\n"
            "Usa /digest para obtener tu resumen ahora."
        ),

        # /digest
        "checking_inbox":   "⏳ Revisando tu bandeja...",
        "gmail_auth_error": "❌ No se pudo conectar a Gmail. Por favor ejecuta /setup de nuevo.",
        "fetch_error":      "❌ No se pudieron obtener los correos. Intenta /setup para reconectarte.",
        "no_emails":        "📭 No hay correos importantes nuevos.",
        "digest_sent":      "Resumen enviado — {total} correo(s) importante(s).",

        # Background jobs
        "gmail_expired":   "Tu autorización de Gmail ha expirado. Ejecuta /setup para reconectarte.",
        "reconnect_error": "❌ Por favor ejecuta /setup para reconectarte.",

        # Alert & digest email messages
        "alert_header":   "⚠️ Correo urgente",
        "from_label":     "De",
        "subject_label":  "Asunto",
        "score_label":    "Puntuación",
        "digest_title":   "Resumen MailPilot — {count} correo(s) importante(s)",

        # /help
        "help_no_question": (
            "¡Pregúntame lo que quieras sobre MailPilot!\n"
            "Ejemplo: /help ¿cómo funcionan las palabras clave?"
        ),
        "help_ai_error": (
            "No pude responder eso ahora. "
            "Intenta /setup para revisar tu configuración o contacta soporte."
        ),

        # /reset
        "history_cleared": "Historial de conversación eliminado.",

        # Fallback
        "unknown_command": (
            "Lo siento, no entendí eso.\n\n"
            "Comandos disponibles:\n"
            "/start  — reiniciar el bot\n"
            "/setup  — conectar Gmail y configurar filtros\n"
            "/status — ver tu configuración y estadísticas de 24 h\n"
            "/digest — obtener los correos importantes de hoy\n"
            "/ping   — verificar que el bot está activo\n"
            "/help   — hacer una pregunta sobre MailPilot\n"
            "/reset  — limpiar el historial de /help\n"
            "/language — cambiar idioma / change language"
        ),
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Return the translated string for lang/key, falling back to 'en'."""
    text = STRINGS.get(lang, STRINGS["en"]).get(key) or STRINGS["en"][key]
    return text.format(**kwargs) if kwargs else text
