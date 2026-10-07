import os
from dotenv import load_dotenv
load_dotenv()


SYMBOL = "XAUUSD"
LOT = 0.01
GRID_DISTANCE = 3.0
TARGET_USD = 75
MAX_ORDERS = 15

MAX_BUY_VOLUME = 0.10
MAX_SELL_VOLUME = 0.10
MAX_NET_VOLUME = 0.04

TRAILING_PERCENT = 0.80
# 0.80 = permite devolver no máximo 20% do lucro máximo

# Não será mais usado pelo trailing
# PROFIT_TO_CLOSE = 6.0

# CONFIG DO MT5 - VEM DO .ENV - NÃO MEXER
MT5_LOGIN = int(os.getenv("MT5_LOGIN"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD")
MT5_SERVER = os.getenv("MT5_SERVER")
MT5_PATH = os.getenv("MT5_PATH") or None