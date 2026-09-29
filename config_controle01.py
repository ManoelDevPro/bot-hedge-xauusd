import os
from dotenv import load_dotenv
load_dotenv()


# ============================================================
# ⚖️ LIMITADORES DE EXPOSIÇÃO
# ============================================================

# Volume máximo acumulado de BUY
MAX_BUY_VOLUME = 0.10

# Volume máximo acumulado de SELL
MAX_SELL_VOLUME = 0.10

# Diferença máxima permitida entre BUY e SELL
MAX_NET_VOLUME = 0.04