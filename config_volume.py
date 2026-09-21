import os
from dotenv import load_dotenv
load_dotenv()


# CONFIG DA ESTRATÉGIA - PODE MEXER
SYMBOL = "XAUUSD"
LOT = 0.01
GRID_DISTANCE = 12.0
PROFIT = 12.0
TARGET_USD = 75 #   Meta de lucro total para reiniciar o bot
MAX_ORDERS = 8
TRAILING_PERCENT = 0.70
# 0.70 = permite devolver no máximo 30% do lucro máximo

# Não será mais usado pelo trailing
# PROFIT_TO_CLOSE = 6.0

# CONFIG DO MT5 - VEM DO .ENV - NÃO MEXER
MT5_LOGIN = int(os.getenv("MT5_LOGIN"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD")
MT5_SERVER = os.getenv("MT5_SERVER")
MT5_PATH = os.getenv("MT5_PATH") or None