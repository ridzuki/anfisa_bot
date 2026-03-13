from pathlib import Path

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

import os
TOKEN = os.getenv("BOT_TOKEN")
print("TOKEN EXISTS:", bool(TOKEN))
print("TOKEN PREFIX:", TOKEN[:10] if TOKEN else "NONE")
PHOTO_DIR = Path("photos")


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
        "Если не сработает, используйте <b>запасной ключ</b>.\n\n"
        "🎀 Вход в квартиру — <b>в холле, дверь с бантом</b>."
    ),
    "food": (
        "🍽️ <b>Еда и кормушка</b>\n\n"
        "⚠️ У Анфисы <b>хронический цистит</b>, поэтому ей можно только "
        "<b>корм для кошек с проблемами с почками</b>.\n\n"
        "🛏️ Автоматическая кормушка находится <b>в спальне</b>.\n"
        "Она выдаёт корм несколько раз в день, всего около <b>50 г в сутки</b>.\n\n"
        "📹 Если кормушка заглючит, я увижу это по камерам.\n"
        "Тогда можно насыпать ей <b>полную миску корма раз в два дня</b>.\n\n"
        "🗄️ В спальне есть <b>шкаф с запасным кормом</b>.\n"
        "🥣 Там же есть <b>1 пауч жидкого корма</b>."
    ),
    "water": (
        "💧 <b>Вода и поилки</b>\n\n"
        "🚰 Автопоилка находится <b>на кухне</b>.\n"
        "Анфиса сейчас редко пьёт из неё.\n\n"
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
        "🗑️ Пакеты для мусора оставим — просто выбрасывайте "
        "их в <b>уличную мусорку</b>.\n\n"
        "😷 Если появится запах — рядом есть "
        "<b>запасной наполнитель</b>."
    ),
    "med": (
        "💊 <b>Аптечка</b>\n\n"
        "🗄️ В <b>комнате</b> есть <b>шкаф</b>.\n"
        "В нём лежит <b>косметичка с лекарствами</b>.\n\n"
        "⚠️ Самое важное лекарство — <b>габапентин</b>, "
        "если начнётся цистит."
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
        ["🏠 Старт"],
        ["1. Как войти"],
        ["2. Еда и кормушка"],
        ["3. Вода и поилки"],
        ["4. Лотки и наполнитель"],
        ["5. Аптечка и остальное"],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


async def send_single_photo(chat_id: int, context: ContextTypes.DEFAULT_TYPE, key: str) -> None:
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


async def send_main_menu(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=chat_id,
        text="🏠 <b>Главное меню</b>\nВыберите нужный раздел кнопками ниже.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


async def send_album(chat_id: int, context: ContextTypes.DEFAULT_TYPE, key: str) -> None:
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
    await send_single_photo(chat_id, context, "welcome")


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    if text == "🏠 Старт":
        await send_single_photo(chat_id, context, "welcome")
    elif text == "1. Как войти":
        await send_album(chat_id, context, "entry")
    elif text == "2. Еда и кормушка":
        await send_album(chat_id, context, "food")
    elif text == "3. Вода и поилки":
        await send_album(chat_id, context, "water")
    elif text == "4. Лотки и наполнитель":
        await send_album(chat_id, context, "trays")
    elif text == "5. Аптечка и остальное":
        await send_album(chat_id, context, "med")
    else:
        await send_main_menu(chat_id, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Ошибка: {context.error}")


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_error_handler(error_handler)

    print("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
