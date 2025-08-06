import logging
from PIL import Image, ImageEnhance
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Словарь для хранения состояния пользователей
user_data = {}

# Команда /start — показывает кнопки яркости
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🔆 +30%", callback_data='brightness_30'),
            InlineKeyboardButton("🔆 +50%", callback_data='brightness_50'),
        ],
        [InlineKeyboardButton("🔢 Своя яркость", callback_data='custom')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите уровень яркости:", reply_markup=reply_markup)

# Обработка нажатий на кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data.startswith('brightness_'):
        percent = int(query.data.split('_')[1])
        user_data[user_id] = {'brightness': percent}
        await query.message.reply_text(f"Теперь отправьте фото для увеличения яркости на {percent}%")

    elif query.data == 'custom':
        user_data[user_id] = {'awaiting_custom': True}
        await query.message.reply_text("Введите желаемое значение яркости в процентах (например: 45):")

# Обработка пользовательского ввода яркости
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id in user_data and user_data[user_id].get('awaiting_custom'):
        try:
            percent = int(text)
            if 0 < percent <= 500:
                user_data[user_id] = {'brightness': percent}
                await update.message.reply_text(f"Установлена яркость: +{percent}%. Теперь отправьте фото.")
            else:
                await update.message.reply_text("Введите число от 1 до 500.")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите число.")

# Обработка фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Проверка — выбрал ли пользователь яркость
    if user_id not in user_data or 'brightness' not in user_data[user_id]:
        await update.message.reply_text("Сначала выберите уровень яркости с помощью /start.")
        return

    # Получаем фото
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = BytesIO()
    await file.download_to_memory(out=file_bytes)
    file_bytes.seek(0)

    # Обработка яркости
    try:
        image = Image.open(file_bytes)
        enhancer = ImageEnhance.Brightness(image)
        brightness_factor = 1 + (user_data[user_id]['brightness'] / 100)
        enhanced_image = enhancer.enhance(brightness_factor)

        # Сохраняем и отправляем обратно
        output_bytes = BytesIO()
        output_bytes.name = 'brightened.jpg'
        enhanced_image.save(output_bytes, format='JPEG')
        output_bytes.seek(0)

        await update.message.reply_photo(photo=output_bytes, caption=f"Готово! Яркость увеличена на {user_data[user_id]['brightness']}%")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при обработке изображения: {e}")

# Главная функция запуска
def main():
    TOKEN = "8071436957:AAEiuBZT9vGCG5iRAS8unLylh1JEvBt7Yf8"  # 🔁 Замените на ваш токен
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()