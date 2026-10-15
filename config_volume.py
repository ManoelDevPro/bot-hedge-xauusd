import os
from dotenv import load_dotenv
load_dotenv()


# CONFIG DA ESTRATÉGIA - PODE MEXER
SYMBOL = "XAUUSD"
LOT = 0.01
GRID_DISTANCE = 8.0
PROFIT = 6
TARGET_USD = 10 #   Meta de lucro total para reiniciar o bot
MAX_ORDERS = 8
STOP_LOSS_USD = -2
TRAILING_PERCENT = 0.80
# 0.80 = permite devolver no máximo 20% do lucro máximo

# Não será mais usado pelo trailing
# PROFIT_TO_CLOSE = 6.0

# CONFIG DO MT5 - VEM DO .ENV - NÃO MEXER
MT5_LOGIN = int(os.getenv("MT5_LOGIN"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD")
MT5_SERVER = os.getenv("MT5_SERVER")
MT5_PATH = os.getenv("MT5_PATH") or None