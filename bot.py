from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from coingecko_api import CoinGeckoAPI
from repository import SQLiteRepository
import asyncio

API_TOKEN = '7949340966:AAEmCSueXufG81e1a0fbg1WABsHk_KmeFwQ'

# Initialize bot and router
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
router = Router()

# Initialize CoinGecko API and SQLite repository
coingecko = CoinGeckoAPI()
repo = SQLiteRepository('crypto_alerts.db')

# Define states
class CoinLimit(StatesGroup):
    selecting_coin = State()
    setting_target = State()
    choosing_alert_type = State()

@router.message(Command(commands=['start', 'help']))
async def send_welcome(message: types.Message):
    await message.reply("Welcome! Use /coin_limits to set up a new price alert.")

@router.message(Command(commands=['coin_limits']))
async def coin_limits(message: types.Message, state: FSMContext):
    coins = coingecko.get_top_coins()

    kb = [[types.KeyboardButton(text=coin['id'])] for coin in coins[:10]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.reply("Please select a coin:", reply_markup=keyboard)
    await state.set_state(CoinLimit.selecting_coin)

@router.message(CoinLimit.selecting_coin)
async def process_coin(message: types.Message, state: FSMContext):
    await state.update_data(selected_coin=message.text.lower())
    await message.reply("Please enter the target price:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(CoinLimit.setting_target)

@router.message(CoinLimit.setting_target)
async def process_target(message: types.Message, state: FSMContext):
    try:
        target_price = float(message.text)
        await state.update_data(target_price=target_price)

        kb = [[types.KeyboardButton(text="Higher")], [types.KeyboardButton(text="Lower")]]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.reply("When should I notify you? When the price is higher or lower than the target?", reply_markup=keyboard)
        await state.set_state(CoinLimit.choosing_alert_type)
    except ValueError:
        await message.reply("Please enter a valid number for the target price.")

@router.message(CoinLimit.choosing_alert_type)
async def process_alert_type(message: types.Message, state: FSMContext):
    alert_type = message.text.lower()
    if alert_type not in ['higher', 'lower']:
        await message.reply("Please choose either 'Higher' or 'Lower'.")
        return

    user_data = await state.get_data()
    user_id = message.from_user.id
    coin = user_data['selected_coin']
    target_price = user_data['target_price']

    repo.add_alert(user_id, coin, target_price, alert_type)

    await message.reply(
        f"Alert set successfully!\n"
        f"Coin: {coin}\n"
        f"Target Price: ${target_price}\n"
        f"Alert Type: {alert_type}",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()

async def check_alerts():
    while True:
        alerts = repo.get_all_alerts()
        for alert in alerts:
            user_id, coin, target_price, alert_type = alert
            current_price = coingecko.get_price(coin).get('usd')

            if not current_price:
                continue  # Skip if the current price is not available

            if (alert_type == 'higher' and current_price > target_price) or \
               (alert_type == 'lower' and current_price < target_price):
                await bot.send_message(
                    user_id,
                    f"Alert triggered for {coin}!\n"
                    f"Current price: ${current_price}\n"
                    f"Target price: ${target_price}"
                )
                repo.remove_alert(user_id, coin)
        await asyncio.sleep(60)  # Check every minute


@router.message(Command(commands=['my_alerts']))
async def show_my_alerts(message: types.Message):
    user_id = message.from_user.id
    alerts = repo.get_user_alerts(user_id)
    
    if not alerts:
        await message.reply("You don't have any active alerts.")
        return

    response = "Your active alerts:\n\n"
    for alert in alerts:
        coin, target_price, alert_type = alert
        current_price = coingecko.get_price(coin).get('usd')
        
        if current_price:
            price_diff = abs(current_price - target_price)
            percentage_diff = (price_diff / target_price) * 100
            
            response += (
                f"🪙 Coin: {coin.upper()}\n"
                f"🎯 Target: ${target_price:.2f}\n"
                f"📊 Current: ${current_price:.2f}\n"
                f"📈 Alert type: {alert_type}\n"
                f"📉 Difference: ${price_diff:.2f} ({percentage_diff:.2f}%)\n\n"
            )
        else:
            response += (
                f"🪙 Coin: {coin.upper()}\n"
                f"🎯 Target: ${target_price:.2f}\n"
                f"📈 Alert type: {alert_type}\n"
                f"❗ Current price unavailable\n\n"
            )

    await message.reply(response)

async def main():
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    
    asyncio.create_task(check_alerts())
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())