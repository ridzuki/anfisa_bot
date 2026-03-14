from collections import defaultdict
from pathlib import Path
import os
import html
import logging
import asyncio

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

if not OWNER_CHAT_ID:
    raise ValueError("OWNER_CHAT_ID не найден в переменных окружения")

OWNER_CHAT_ID = int(OWNER_CHAT_ID)

PHOTO_DIR = Path("photos")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MEDIA_GROUP_BUFFER = defaultdict(list)
MEDIA_GROUP_TASKS = {}


TEXTS = {
    "welcome": (
        "🐾 <b>Привет! Это мини-бот помощник по Анфисочке</b>\n\n"
        "💛 Спасибо вам большое за помощь и заботу о ней.\n\n"
        "🥒 Анфисонька очень любит <b>огурчики</b>, <b>перчики</b> и, конечно, <b>внимание</b>.\n"
        "Если будет возможность, пожалуйста, приходите к Анфушке <b>каждый день</b> просто погладить её.\n\n"
        "🧼 Лоточки желательно убирать примерно <b>раз в 2 дня</b>.\n\n"
        "👇 Нажимайте кнопки ниже, чтобы открыть нужный раздел."
    ),

    "entry": (
        "🚪 <b>Как войти</b>\n\n"
        "🔔 Домофон иногда <b>не открывает дверь</b>. "
        "Если не сработает — используйте <b>запасной ключ</b>.\n\n"
        "🎀 Вход в квартиру — <b>в холле, дверь с бантом</b>.\n\n"
        "⚠️<b>🚪Перед уходом</b>\n\n"
        "Пожалуйста, когда будете уходить, <b>не забудьте закрыть двери на ключ</b>.\n"
        "Нужно закрыть:\n"
        "• <b>дверь квартиры</b>\n"
        "• <b>дверь в холл</b>\n\n"
        "Сейчас участились случаи взломов, поэтому лучше обезопасить квартиру дополнитель закрыв входную группу(там где домофон).\n"
        "Дверь в холл закрывается <b>обычным ключом</b>.\n"
        "⚠️ Обратите внимание: если закрыть её на ключ, <b>открыть её через NFC-ключ домофона уже не получится</b>."
    ),

    "food": (
        "🍽️ <b>Еда и кормушка</b>\n\n"
        "⚠️ У Анфисы <b>хронический цистит</b>, поэтому ей можно только "
        "<b>корм для кошек с проблемами с почками</b> и немного овощей.\n\n"
        "🛏️ Автоматическая кормушка находится <b>в спальне</b>.\n"
        "Она выдаёт корм несколько раз в день, всего около <b>50 г в сутки</b>.\n\n"
        "📹 Если кормушка заглючит, я увижу это по камерам.\n"
        "Если это случится - я вас предупрежу и тогда можно насыпать ей <b>полную миску корма раз в два дня</b>.\n\n"
        "🗄️ В спальне есть <b>шкаф с запасным кормом</b>.\n"
        "🥣 Там же есть <b>1 пауч жидкого корма</b>. Дайте ей его в любой день весь.\n\n"
        "🥒 Анфиса очень любит <b>огурцы и сладкие перцы</b>.\n"
        "Если будет возможность — дайте ей <b>огурчик\\перчик</b>, "
        "она этому очень радуется. Но <b>не больше 1 огурца\\половины болгарского перца</b> в сутки\n"
        "Найти огурцы и перцы можете в холодильнике. Если их не останется - по возможности купите, я вам скину, когда приеду деньги.\n\n"
        "<b>Заранее огромное спасибо!</b>"
    ),

    "water": (
        "💧 <b>Вода и поилки</b>\n\n"
        "🚰 Автопоилка находится <b>на кухне</b>.\n"
        "Там же стоит <b>10-литровая бутылка питьевой воды</b>.\n\n"
        "Анфиса сейчас редко пьёт из автопоилки, но лучше пусть будет. Если вы заметите что автопоилка мигает красным - поставьте ее на зарядку, пожалуйста.\n\n"
        "🏠 В комнате стоит <b>обычная ёмкость с водой</b>.\n"
        "Воду там нужно менять <b>раз в 2 дня</b>.\n\n"
        "🧽 Автопоилку очень прошу <b>помыть 25–26 числа</b> "
        "и налить <b>новой воды</b>."
    ),

    "trays": (
        "🧻 <b>Лотки и наполнитель</b>\n\n"
        "🛁 Лотки находятся <b>в ванной</b>.\n\n"
        "♻️ Полностью менять наполнитель <b>не нужно</b> — "
        "их нужно только <b>чистить</b>.\n\n"
        "🗑️ Пакеты для мусора оставим — "
        "просто выбрасывайте их в <b>уличную мусорку</b>.\n\n"
        "😷 Если появится запах — рядом есть "
        "<b>запасной наполнитель и большие пакеты для мусора</b>."
    ),

    "med": (
        "💊 <b>Аптечка</b>\n\n"
        "🗄️ В <b>комнате</b> есть <b>шкаф</b>.\n"
        "В нём лежит <b>косметичка с лекарствами</b>.\n\n"
        "⚠️ Самое важное лекарство — <b>габапентин</b>, "
        "если начнётся цистит."
    ),
    "visit_prompt": (
        "📸 <b>Фото визита</b>\n\n"
        "Пожалуйста, отправьте фото котёнка.\n"
        "Я перешлю его хозяйке в личку."
    ),
    "visit_success": (
        "✅ Фото отправлено хозяйке.\n"
        "Спасибо большое!"
    ),
}


PHOTOS = {
    "welcome": [
        PHOTO_DIR / "anfi.jpg",
    ],

    "entry": [
        PHOTO_DIR / "domofon.jpg",
        PHOTO_DIR / "door1.jpg",
        PHOTO_DIR / "hall.jpg",
        PHOTO_DIR / "door2.jpg",
    ],

    "food": [
        PHOTO_DIR / "feeder.jpg",
        PHOTO_DIR / "shkaf.jpg",
        PHOTO_DIR / "shkaf_food.jpg",
        PHOTO_DIR / "shkaf_food_2.jpg",
    ],

    "water": [
        PHOTO_DIR / "water1.jpg",
        PHOTO_DIR / "water1_zoom.jpg",
        PHOTO_DIR / "water2.jpg",
    ],

    "trays": [
        PHOTO_DIR / "lotki.jpg",
        PHOTO_DIR / "lotki_zoom.jpg",
        PHOTO_DIR / "lotki_zoom2.jpg",
    ],

    "med": [
        PHOTO_DIR / "shkaf.jpg",
        PHOTO_DIR / "shkaf_farm.jpg",
    ],
}


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        ["🚪 Как войти", "🍽 Еда и кормушка"],
        ["💧 Вода и поилки", "🧻 Лотки и наполнитель"],
        ["💊 Аптечка и остальное", "📸 Ходил(а) к котёнку"],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


def user_title(update: Update) -> str:
    user = update.effective_user
    if not user:
        return "Неизвестный пользователь"
    full_name = " ".join(
        part for part in [user.first_name, user.last_name] if part
    ).strip()
    username = f"@{user.username}" if user.username else "без username"
    return f"{full_name or 'Без имени'} ({username}, id={user.id})"


async def notify_owner(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    try:
        await context.bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text=text,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("Не удалось отправить лог владельцу: %s", e)


async def log_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    chat = update.effective_chat
    chat_id = chat.id if chat else "unknown"
    safe_action = html.escape(action)
    safe_user = html.escape(user_title(update))
    text = (
        f"📋 <b>Действие в боте</b>\n\n"
        f"<b>Пользователь:</b> {safe_user}\n"
        f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
        f"<b>Действие:</b> {safe_action}"
    )
    await notify_owner(context, text)


async def forward_user_text_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    safe_user = html.escape(user_title(update))
    safe_text = html.escape(text)
    chat_id = update.effective_chat.id

    await context.bot.send_message(
        chat_id=OWNER_CHAT_ID,
        text=(
            f"💬 <b>Сообщение от пользователя</b>\n\n"
            f"<b>Пользователь:</b> {safe_user}\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"<b>Текст:</b> {safe_text}"
        ),
        parse_mode="HTML",
    )


async def flush_media_group(context: ContextTypes.DEFAULT_TYPE, media_group_id: str) -> None:
    await asyncio.sleep(1.5)

    items = MEDIA_GROUP_BUFFER.pop(media_group_id, [])
    MEDIA_GROUP_TASKS.pop(media_group_id, None)

    if not items:
        return

    first = items[0]
    update = first["update"]
    safe_user = html.escape(user_title(update))
    chat_id = update.effective_chat.id
    is_visit = first["is_visit"]

    media = []
    for i, item in enumerate(items):
        file_id = item["file_id"]
        caption = item["caption"]

        if i == 0:
            if is_visit:
                first_caption = (
                    f"📸 <b>Фото от посетителя</b>\n\n"
                    f"<b>Пользователь:</b> {safe_user}\n"
                    f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
                    f"<b>Альбом:</b> <code>{media_group_id}</code>\n"
                    f"<b>Подпись:</b> {html.escape(caption) if caption else '—'}"
                )
            else:
                first_caption = (
                    f"🖼 <b>Альбом от пользователя</b>\n\n"
                    f"<b>Пользователь:</b> {safe_user}\n"
                    f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
                    f"<b>Альбом:</b> <code>{media_group_id}</code>\n"
                    f"<b>Подпись:</b> {html.escape(caption) if caption else '—'}"
                )

            media.append(
                InputMediaPhoto(
                    media=file_id,
                    caption=first_caption,
                    parse_mode="HTML",
                )
            )
        else:
            media.append(InputMediaPhoto(media=file_id))

    await context.bot.send_media_group(
        chat_id=OWNER_CHAT_ID,
        media=media,
    )

    if is_visit:
        await log_action(update, context, f"Пользователь отправил фото визита альбомом ({len(items)} фото)")
    else:
        await log_action(update, context, f"Пользователь отправил альбом из {len(items)} фото")


async def handle_user_photo_forwarding(update: Update, context: ContextTypes.DEFAULT_TYPE, is_visit: bool) -> None:
    if not update.message or not update.message.photo:
        return

    media_group_id = update.message.media_group_id
    caption = update.message.caption or ""
    file_id = update.message.photo[-1].file_id

    if media_group_id:
        MEDIA_GROUP_BUFFER[media_group_id].append(
            {
                "file_id": file_id,
                "caption": caption,
                "update": update,
                "is_visit": is_visit,
            }
        )

        if media_group_id not in MEDIA_GROUP_TASKS:
            MEDIA_GROUP_TASKS[media_group_id] = asyncio.create_task(
                flush_media_group(context, media_group_id)
            )
        return

    safe_user = html.escape(user_title(update))
    chat_id = update.effective_chat.id
    safe_caption = html.escape(caption)

    if is_visit:
        caption_text = (
            f"📸 <b>Фото от посетителя</b>\n\n"
            f"<b>Пользователь:</b> {safe_user}\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"<b>Подпись:</b> {safe_caption if safe_caption else '—'}"
        )
    else:
        caption_text = (
            f"🖼 <b>Фото от пользователя</b>\n\n"
            f"<b>Пользователь:</b> {safe_user}\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"<b>Подпись:</b> {safe_caption if safe_caption else '—'}"
        )

    await context.bot.send_photo(
        chat_id=OWNER_CHAT_ID,
        photo=file_id,
        caption=caption_text,
        parse_mode="HTML",
    )

    if is_visit:
        await log_action(update, context, "Пользователь отправил фото визита")
    else:
        await log_action(update, context, "Пользователь отправил фото")


async def forward_user_sticker_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.sticker:
        return

    safe_user = html.escape(user_title(update))
    chat_id = update.effective_chat.id
    emoji = html.escape(update.message.sticker.emoji or "—")

    await context.bot.send_sticker(
        chat_id=OWNER_CHAT_ID,
        sticker=update.message.sticker.file_id,
    )

    await context.bot.send_message(
        chat_id=OWNER_CHAT_ID,
        text=(
            f"🎭 <b>Стикер от пользователя</b>\n\n"
            f"<b>Пользователь:</b> {safe_user}\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"<b>Emoji:</b> {emoji}"
        ),
        parse_mode="HTML",
    )


async def forward_user_video_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.video:
        return

    safe_user = html.escape(user_title(update))
    chat_id = update.effective_chat.id
    caption = update.message.caption or ""
    safe_caption = html.escape(caption)

    await context.bot.send_video(
        chat_id=OWNER_CHAT_ID,
        video=update.message.video.file_id,
        caption=(
            f"🎬 <b>Видео от пользователя</b>\n\n"
            f"<b>Пользователь:</b> {safe_user}\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"<b>Подпись:</b> {safe_caption if safe_caption else '—'}"
        ),
        parse_mode="HTML",
    )


async def forward_user_voice_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.voice:
        return

    safe_user = html.escape(user_title(update))
    chat_id = update.effective_chat.id

    await context.bot.send_voice(
        chat_id=OWNER_CHAT_ID,
        voice=update.message.voice.file_id,
        caption=(
            f"🎤 <b>Голосовое от пользователя</b>\n\n"
            f"<b>Пользователь:</b> {safe_user}\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>"
        ),
        parse_mode="HTML",
    )


async def forward_user_video_note_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.video_note:
        return

    safe_user = html.escape(user_title(update))
    chat_id = update.effective_chat.id

    await context.bot.send_video_note(
        chat_id=OWNER_CHAT_ID,
        video_note=update.message.video_note.file_id,
    )

    await context.bot.send_message(
        chat_id=OWNER_CHAT_ID,
        text=(
            f"📹 <b>Видеосообщение от пользователя</b>\n\n"
            f"<b>Пользователь:</b> {safe_user}\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>"
        ),
        parse_mode="HTML",
    )


async def forward_user_document_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.document:
        return

    safe_user = html.escape(user_title(update))
    chat_id = update.effective_chat.id
    caption = update.message.caption or ""
    safe_caption = html.escape(caption)
    filename = html.escape(update.message.document.file_name or "без имени")

    await context.bot.send_document(
        chat_id=OWNER_CHAT_ID,
        document=update.message.document.file_id,
        caption=(
            f"📄 <b>Документ от пользователя</b>\n\n"
            f"<b>Пользователь:</b> {safe_user}\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"<b>Файл:</b> {filename}\n"
            f"<b>Подпись:</b> {safe_caption if safe_caption else '—'}"
        ),
        parse_mode="HTML",
    )


async def send_single_photo(chat_id: int, context: ContextTypes.DEFAULT_TYPE, key: str):
    text = TEXTS[key]
    photo_path = PHOTOS[key][0]

    with open(photo_path, "rb") as photo:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )


async def send_album(chat_id: int, context: ContextTypes.DEFAULT_TYPE, key: str):
    text = TEXTS[key]
    photo_paths = PHOTOS[key]

    media = []
    files = []

    try:
        for i, path in enumerate(photo_paths):
            f = open(path, "rb")
            files.append(f)

            if i == 0:
                media.append(InputMediaPhoto(media=f, caption=text, parse_mode="HTML"))
            else:
                media.append(InputMediaPhoto(media=f))

        if len(media) == 1:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=files[0],
                caption=text,
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(),
            )
        else:
            await context.bot.send_media_group(
                chat_id=chat_id,
                media=media,
            )

    finally:
        for f in files:
            f.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    context.user_data["awaiting_visit_photo"] = False
    context.user_data["visit_success_sent"] = False
    await send_single_photo(chat_id, context, "welcome")
    await log_action(update, context, "/start")
    logger.info("MY CHAT ID: %s", update.effective_chat.id)


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if text == "🚪 Как войти":
        context.user_data["awaiting_visit_photo"] = False
        context.user_data["visit_success_sent"] = False
        await send_album(chat_id, context, "entry")
        await log_action(update, context, "Открыт раздел: Как войти")

    elif text == "🍽 Еда и кормушка":
        context.user_data["awaiting_visit_photo"] = False
        context.user_data["visit_success_sent"] = False
        await send_album(chat_id, context, "food")
        await log_action(update, context, "Открыт раздел: Еда и кормушка")

    elif text == "💧 Вода и поилки":
        context.user_data["awaiting_visit_photo"] = False
        context.user_data["visit_success_sent"] = False
        await send_album(chat_id, context, "water")
        await log_action(update, context, "Открыт раздел: Вода и поилки")

    elif text == "🧻 Лотки и наполнитель":
        context.user_data["awaiting_visit_photo"] = False
        context.user_data["visit_success_sent"] = False
        await send_album(chat_id, context, "trays")
        await log_action(update, context, "Открыт раздел: Лотки и наполнитель")

    elif text == "💊 Аптечка и остальное":
        context.user_data["awaiting_visit_photo"] = False
        context.user_data["visit_success_sent"] = False
        await send_album(chat_id, context, "med")
        await log_action(update, context, "Открыт раздел: Аптечка и остальное")

    elif text == "📸 Ходил(а) к котёнку":
        context.user_data["awaiting_visit_photo"] = True
        context.user_data["visit_success_sent"] = False
        await context.bot.send_message(
            chat_id=chat_id,
            text=TEXTS["visit_prompt"],
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        await log_action(update, context, "Нажата кнопка: Ходил(а) к котёнку")

    else:
        context.user_data["awaiting_visit_photo"] = False
        context.user_data["visit_success_sent"] = False
        await send_single_photo(chat_id, context, "welcome")
        await log_action(update, context, f"Отправлен произвольный текст: {text}")
        await forward_user_text_to_owner(update, context, text)


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.photo:
        return

    waiting = context.user_data.get("awaiting_visit_photo", False)
    media_group_id = update.message.media_group_id
    chat_id = update.effective_chat.id

    await handle_user_photo_forwarding(update, context, is_visit=waiting)

    if not waiting:
        return

    if media_group_id:
        if not context.user_data.get("visit_success_sent", False):
            context.user_data["visit_success_sent"] = True
            context.user_data["awaiting_visit_photo"] = False
            await context.bot.send_message(
                chat_id=chat_id,
                text=TEXTS["visit_success"],
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(),
            )
        return

    context.user_data["awaiting_visit_photo"] = False
    context.user_data["visit_success_sent"] = False

    await context.bot.send_message(
        chat_id=chat_id,
        text=TEXTS["visit_success"],
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def sticker_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await forward_user_sticker_to_owner(update, context)
    await log_action(update, context, "Пользователь отправил стикер")


async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await forward_user_video_to_owner(update, context)
    await log_action(update, context, "Пользователь отправил видео")


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await forward_user_voice_to_owner(update, context)
    await log_action(update, context, "Пользователь отправил голосовое")


async def video_note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await forward_user_video_note_to_owner(update, context)
    await log_action(update, context, "Пользователь отправил видеосообщение")


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await forward_user_document_to_owner(update, context)
    await log_action(update, context, "Пользователь отправил документ")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Ошибка: %s", context.error)
    try:
        await notify_owner(
            context,
            f"❌ <b>Ошибка в боте</b>\n\n<code>{html.escape(str(context.error))}</code>",
        )
    except Exception:
        pass


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.Sticker.ALL, sticker_handler))
    app.add_handler(MessageHandler(filters.VIDEO, video_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, video_note_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_error_handler(error_handler)

    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
