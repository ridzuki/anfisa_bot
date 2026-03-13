from pathlib import Path
import os
import html
import logging

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

OWNER_CHAT_ID = int(OWNER_CHAT_ID) if OWNER_CHAT_ID else None

PHOTO_DIR = Path("photos")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

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
        "🎀 Вход в квартиру — <b>в холле, дверь с бантом</b>."
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
        "🥣 Там же есть <b>1 пауч жидкого корма</b>.\n\n"
        "🥒 Анфиса очень любит <b>огурцы и сладкие перцы</b>.\n"
        "Если будет возможность — дайте ей <b>огурчик\\перчик</b>, "
        "она этому очень радуется. Но <b>не больше 1 огурца\\половины болгарского перца</b> в сутки"
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
    full_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
    username = f"@{user.username}" if user.username else "без username"
    return f"{full_name or 'Без имени'} ({username}, id={user.id})"


async def notify_owner(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    if not OWNER_CHAT_ID:
        logger.info("OWNER_CHAT_ID не задан, пропускаю отправку владельцу")
        return

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
    await send_single_photo(chat_id, context, "welcome")
    await log_action(update, context, "/start")
    logger.info("MY CHAT ID: %s", update.effective_chat.id)


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Твой chat_id: {chat_id}")
    logger.info("MY CHAT ID via /myid: %s", chat_id)


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if text == "🚪 Как войти":
        await send_album(chat_id, context, "entry")

    elif text == "🍽 Еда и кормушка":
        await send_album(chat_id, context, "food")

    elif text == "💧 Вода и поилки":
        await send_album(chat_id, context, "water")

    elif text == "🧻 Лотки и наполнитель":
        await send_album(chat_id, context, "trays")

    elif text == "💊 Аптечка и остальное":
        await send_album(chat_id, context, "med")

    elif text == "📸 Ходил(а) к котёнку":
        context.user_data["awaiting_visit_photo"] = True
        await context.bot.send_message(
            chat_id=chat_id,
            text=TEXTS["visit_prompt"],
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        await log_action(update, context, "Нажата кнопка: Ходил(а) к котёнку")

    else:
        context.user_data["awaiting_visit_photo"] = False
        await send_single_photo(chat_id, context, "welcome")
        await log_action(update, context, f"Отправлен произвольный текст: {text}")


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.photo:
        return

    chat_id = update.effective_chat.id
    waiting = context.user_data.get("awaiting_visit_photo", False)

    if not waiting:
        await log_action(update, context, "Пользователь отправил фото вне режима отправки визита")
        return

    largest_photo = update.message.photo[-1]
    caption = update.message.caption or ""

    safe_user = html.escape(user_title(update))
    safe_caption = html.escape(caption)

    if OWNER_CHAT_ID:
        await context.bot.send_photo(
            chat_id=OWNER_CHAT_ID,
            photo=largest_photo.file_id,
            caption=(
                f"📸 <b>Фото от посетителя</b>\n\n"
                f"<b>Пользователь:</b> {safe_user}\n"
                f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
                f"<b>Подпись:</b> {safe_caption if safe_caption else '—'}"
            ),
            parse_mode="HTML",
        )

        await notify_owner(
            context,
            (
                f"✅ <b>Фото визита получено</b>\n\n"
                f"<b>От:</b> {safe_user}\n"
                f"<b>Chat ID:</b> <code>{chat_id}</code>"
            ),
        )

    context.user_data["awaiting_visit_photo"] = False

    await context.bot.send_message(
        chat_id=chat_id,
        text=TEXTS["visit_success"],
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )

    await log_action(update, context, "Пользователь отправил фото визита")


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
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_error_handler(error_handler)

    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
