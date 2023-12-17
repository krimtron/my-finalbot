
from slovar import choose_word, bucvar
from utils import display_word
from random import randint, choice

import asyncio
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram import Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder as IB


from models import User

bot = Bot(token='BOT TOKEN')
dp = Dispatcher()


def get_or_create_user(from_user: types.User):
    user_id = from_user.id
    user = User.get_or_none(id = user_id)
    if user is None:
        user = User.create(id = user_id, balance =50)
    return user


shop_items = [
        {"name": "1️⃣Открыть первую букву1️⃣", "price": 60, "callback_data": "shop-open_first_letter"},
        {"name": "🎲Открыть рандомную букву🎲", "price": 50, "callback_data": "shop-open_random_letter"},
        {"name": "🎰Лотерея🎰", "price": 25, "callback_data": "shop-bonus"},
        {"name": "*️⃣Множитель бонуса*️⃣", "price": 80, "callback_data": "shop-bonus_money"},
        {"name": "📷Купівля спроб📷", "price": 10, "callback_data": "shop-bonus_attemps"},
    ]

# ----------------------------------------------------


main_keyboard = IB()
main_keyboard.row(types.InlineKeyboardButton(text="🎮Грати", callback_data="start_game"))
main_keyboard.row(types.InlineKeyboardButton(text="📝Профіль", callback_data="profile"))
#Допомога
main_keyboard.row(types.InlineKeyboardButton(text="💊Допомога", callback_data="help"))

main_back_keyboard = IB()
main_back_keyboard_but =types.InlineKeyboardButton(text='👈 В головне меню', callback_data='main_back')
main_back_keyboard.row(main_back_keyboard_but)

game_keyboard = IB()
game_keyboard.row(types.InlineKeyboardButton(text="💰Магазин", callback_data="shop"))



@dp.message(Command("start"))
async def send_welcome(message: Message):
    user = get_or_create_user(message.from_user)
    text = f'Привіт, {message.from_user.full_name}! Тут ти можеш зіграти в гру "Виселиця".'
    await message.answer(text, reply_markup=main_keyboard.as_markup())
    
@dp.callback_query(F.data == "help")
async def help_menu_call(call: types.CallbackQuery):
    text= f'В цій грі вам потрібно відгадати слово, яке вибере бот. Ви можете відгадувати по одній букві. Якщо ви відгадали букву, то вона з\'явиться на своєму місці. Якщо букви немає в слові, то ви втрачаєте спробу. Якщо ви відгадали слово, то ви виграли. Якщо ви втратили всі спроби, то ви програли.'
    await call.message.edit_text(text, reply_markup=main_back_keyboard.as_markup())

@dp.callback_query(F.data == "profile")
async def profile_menu_call(call: types.CallbackQuery):
    user = get_or_create_user(call.from_user)
    text= f'Ваш баланс: {user.balance}\nВаші перемоги: {user.victory}\nВаші поразки: {user.defeat}\nУровень вашего множителя денег: {user.bonus_multiplier}\nВаш множитель равен: {user.bonus_multiplier / 10}'
    await call.message.edit_text(text, reply_markup=main_back_keyboard.as_markup())
    

@dp.callback_query(F.data == "main_back")
async def main_back_menu_call(call: types.CallbackQuery):
    await call.message.edit_text("Головне меню", reply_markup=main_keyboard.as_markup())


# ----------------------------------------------------


@dp.callback_query(F.data == "start_game")
async def start_game_call(call: types.CallbackQuery):
    user = get_or_create_user(call.from_user)
    if user.is_playing:
        text= f'Ви вже граєте в гру. Давайте я вам нагадаю слово: {display_word(user.word, user.guessed_letters)}\n Введіть букву яку ви хочете відгадати.\nУ вас залишилось спроб: {user.attempts}'
        text+= f'\nВведені літери: {user.guessed_letters}'
        await call.message.edit_text(text)
        return
    user.is_playing = True
    user.word = choose_word()
    user.attempts = 10
    user.guessed_letters = ""
    user.save()
    text = f'Ви почали гру. Введіть букву яку ви хочете відгадати.\nУ вас залишилось спроб: {user.attempts}\n{display_word(user.word, user.guessed_letters)}'
    await call.message.edit_text(text)



@dp.message()
async def some_message(message: types.Message):
    user = get_or_create_user(message.from_user)
    if not user.is_playing:
        await message.answer("Давайте пограємо в Виселица! \n Перейдіть в головне меню", reply_markup=main_back_keyboard.as_markup())
        return
    


    user_answer = message.text.lower()[0]
    if user_answer not in bucvar:
        await message.answer("Ви ввели недопустимий символ. Тільки Українські літери.")
        return
    
    if user_answer in user.guessed_letters:
        await message.answer("Ви вже ввели цю літеру. Спробуйте інший.")
        return
    
    user.guessed_letters = user.guessed_letters+user_answer
    user.save()
    zapataia = ", ".join(user.guessed_letters)
    if user_answer not in user.word:
        user.attempts -= 1
        user.save()
        text = f"Ви не вгадали!\nУ вас залишилось спроб: {user.attempts}\n{display_word(user.word, user.guessed_letters)}\nВикористанні букви {zapataia}"
        if user.attempts == 0: # перевірка чи спроби закінчилися
            user.is_playing = False
            user.defeat += 1
            user.save()
            text = f"На жаль, ви програли. Приховане слово було: {user.word}"
            await message.answer(text, reply_markup=main_back_keyboard.as_markup())
            return
    else:
        text = f"Ви вгадали!\n{display_word(user.word, user.guessed_letters)}\nВикористанні букви {zapataia}"
        if "_" not in display_word(user.word, user.guessed_letters): # перевірка чи всі букви відгадані то виграш
            user.is_playing = False
            user.balance = user.balance + 30 + (30 * user.bonus_multiplier / 10)
            user.victory += 1 
            user.save()
            text = f"Вітаємо, ви вгадали слово: {user.word}"
            await message.answer(text, reply_markup=main_back_keyboard.as_markup())
            return
    
    
    await message.answer(text, reply_markup=game_keyboard.as_markup())
    


@dp.callback_query(F.data == "shop")
async def shop_menu_call(call: types.CallbackQuery):
    user = get_or_create_user(call.from_user)
    if user is None or not user.is_playing:
        await call.message.edit_text("Ви не граєте в гру. Почніть гру в головному меню.")
        return
    
    shop_items_text = "\n".join([f"{item['name']} - {item['price']}💰" for item in shop_items])
    shop_keyboard = IB()
    shop_keyboard.row(types.InlineKeyboardButton(text="👈 Назад", callback_data="game_back"))
    for item in shop_items:
        shop_keyboard.row(types.InlineKeyboardButton(text=item["name"], callback_data=item["callback_data"]))


    text = f"=== Магазин ===\n{shop_items_text}\nВаш баланс: {user.balance}💰\nДля покупки нажмите на кнопку."
    await call.message.edit_text(text, reply_markup=shop_keyboard.as_markup())
    
@dp.callback_query(F.data == "game_back")
async def game_back_menu_call(call: types.CallbackQuery):
    user = get_or_create_user(call.from_user)
    if user.is_playing:
        text= f'Ви вже граєте в гру. Давайте я вам нагадаю слово: {display_word(user.word, user.guessed_letters)}\n Введіть букву яку ви хочете відгадати.\nУ вас залишилось спроб: {user.attempts}'
        text+= f'\nВведені літери: {user.guessed_letters}'
        await call.message.edit_text(text, reply_markup=game_keyboard.as_markup())
        return
    await call.message.edit_text("Головне меню", reply_markup=main_keyboard.as_markup())
    
    
@dp.callback_query(F.data.startswith("shop-"))
async def shop_item_call(call: types.CallbackQuery):
    user = get_or_create_user(call.from_user)
    if user is None:
        await call.message.edit_text("Ви не граєте в гру. Почніть гру в головному меню.", reply_markup=main_keyboard.as_markup())
        return
    
    item_name = call.data.split("-")[1]
    
    item = next((item for item in shop_items if item["callback_data"] == call.data), None) # пошук товару в магазині
    if item is None:
        await call.answer("Товар не знайдено\nСпробуйте пізніше!", show_alert=True)
        return

    if user.balance < item["price"]:
        await call.answer("У вас недостатньо коштів", show_alert=True)
        return
    
    if item_name == "bonus":
        bonus = randint(2, 50)
        user.balance += bonus
        user.balance -= item["price"]
        user.save()
        await call.answer(f'Ви отримали бонус: {bonus}💰\nВаш баланс: {user.balance}💰\nВаш профит: {bonus - 25}', show_alert=True)
        return
    if item_name == "open_first_letter":
        user.balance -= item["price"]
        user.guessed_letters = user.guessed_letters+user.word[0]
        user.save()
        text = f'Перша буква: {user.word[0]}\n{display_word(user.word, user.guessed_letters)}'
        await call.answer(text, show_alert=True)
        return
    if item_name == "open_random_letter":
        user.balance -= item["price"]
        user.guessed_letters = user.guessed_letters+choice(user.word)
        user.save()
        text = f'Рандомна буква: {user.word[0]}\n{display_word(user.word, user.guessed_letters)}'
        await call.answer(text, show_alert=True)
        return
    if item_name == "bonus_money":
        user.balance -= item["price"]
        user.bonus_multiplier += 1
        text = f'Уровень вашего множителя за победу раваен: {user.bonus_multiplier}'
        user.save()
        await call.answer(text, show_alert=True)
        return
    if item_name == "bonus_attemps":
        user.balance -= item["price"]
        user.attempts += 1
        text = f'Ваші спроби рівні: {user.attempts}'
        user.save()
        await call.answer(text, show_alert=True)
        return

        

        
async def main():
    print("Starting bot...")
    print("Bot username: @{}".format((await bot.me())))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
