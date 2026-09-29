import MetaTrader5 as mt5
import logging

from config_volume import (
    PROFIT,
    TRAILING_PERCENT,
    TARGET_USD,
    MAX_ORDERS,
    GRID_DISTANCE,
    LOT,
    MAX_BUY_VOLUME,
    MAX_SELL_VOLUME,
    MAX_NET_VOLUME
)


# ============================================================
# 🧠 MEMÓRIA DA ESTRATÉGIA
# ============================================================

max_profit_seen = {}


# ============================================================
# 📊 CÁLCULO DE VOLUME
# ============================================================

def calcular_volumes(positions):

    buy_volume = 0.0
    sell_volume = 0.0

    for pos in positions:

        if pos.type == mt5.POSITION_TYPE_BUY:

            buy_volume += pos.volume

        elif pos.type == mt5.POSITION_TYPE_SELL:

            sell_volume += pos.volume

    return buy_volume, sell_volume


# ============================================================
# ⚖️ EXPOSIÇÃO LÍQUIDA
# ============================================================

def calcular_net_volume(
    buy_volume,
    sell_volume
):

    return buy_volume - sell_volume


# ============================================================
# 🧠 ANÁLISE DE PRESSÃO
# ============================================================

def analisar_volume(
    buy_volume,
    sell_volume
):

    if buy_volume > sell_volume:

        return "BUY_PRESSURE"

    elif sell_volume > buy_volume:

        return "SELL_PRESSURE"

    else:

        return "BALANCED"


# ============================================================
# 🛡️ LIMITADOR PARA NOVO BUY
# ============================================================

def pode_abrir_buy(
    buy_volume,
    sell_volume
):

    # --------------------------------------------------------
    # LIMITE ABSOLUTO DE BUY
    # --------------------------------------------------------

    if buy_volume + LOT > MAX_BUY_VOLUME:

        logging.warning(
            f"🛡️ BUY BLOQUEADO | "
            f"BuyVol={buy_volume:.2f} | "
            f"Próximo={buy_volume + LOT:.2f} | "
            f"Limite={MAX_BUY_VOLUME:.2f}"
        )

        return False

    # --------------------------------------------------------
    # CONTROLE DE EXPOSIÇÃO LÍQUIDA
    # --------------------------------------------------------

    net_volume = (
        buy_volume
        - sell_volume
    )

    novo_net = (
        net_volume
        + LOT
    )

    if novo_net > MAX_NET_VOLUME:

        logging.warning(
            f"🛡️ BUY BLOQUEADO | "
            f"Net atual={net_volume:.2f} | "
            f"Net novo={novo_net:.2f} | "
            f"Limite={MAX_NET_VOLUME:.2f}"
        )

        return False

    return True


# ============================================================
# 🛡️ LIMITADOR PARA NOVO SELL
# ============================================================

def pode_abrir_sell(
    buy_volume,
    sell_volume
):

    # --------------------------------------------------------
    # LIMITE ABSOLUTO DE SELL
    # --------------------------------------------------------

    if sell_volume + LOT > MAX_SELL_VOLUME:

        logging.warning(
            f"🛡️ SELL BLOQUEADO | "
            f"SellVol={sell_volume:.2f} | "
            f"Próximo={sell_volume + LOT:.2f} | "
            f"Limite={MAX_SELL_VOLUME:.2f}"
        )

        return False

    # --------------------------------------------------------
    # CONTROLE DE EXPOSIÇÃO LÍQUIDA
    # --------------------------------------------------------

    net_volume = (
        buy_volume
        - sell_volume
    )

    novo_net = (
        net_volume
        - LOT
    )

    if novo_net < -MAX_NET_VOLUME:

        logging.warning(
            f"🛡️ SELL BLOQUEADO | "
            f"Net atual={net_volume:.2f} | "
            f"Net novo={novo_net:.2f} | "
            f"Limite={MAX_NET_VOLUME:.2f}"
        )

        return False

    return True


# ============================================================
# 📊 RELATÓRIO DE EXPOSIÇÃO
# ============================================================

def registrar_exposicao(
    buy_volume,
    sell_volume
):

    net_volume = (
        buy_volume
        - sell_volume
    )

    logging.info(
        f"⚖️ EXPOSIÇÃO | "
        f"BUY={buy_volume:.2f} | "
        f"SELL={sell_volume:.2f} | "
        f"NET={net_volume:+.2f}"
    )


# ============================================================
# 🎯 TRAILING PROFIT
# ============================================================

def processar_trailing(
    positions,
    close_position
):

    for pos in positions:

        ticket = pos.ticket

        # ----------------------------------------------------
        # PRIMEIRA VEZ
        # ----------------------------------------------------

        if ticket not in max_profit_seen:

            max_profit_seen[ticket] = pos.profit

        # ----------------------------------------------------
        # ATUALIZA MÁXIMO
        # ----------------------------------------------------

        if pos.profit > max_profit_seen[ticket]:

            max_profit_seen[ticket] = pos.profit

        max_profit = max_profit_seen[ticket]

        # ----------------------------------------------------
        # TRAILING ATIVA APÓS PROFIT
        # ----------------------------------------------------

        if max_profit >= PROFIT:

            trailing_level = (
                max_profit
                * TRAILING_PERCENT
            )

            # ------------------------------------------------
            # RECUO DO LUCRO
            # ------------------------------------------------

            if pos.profit <= trailing_level:

                tipo = (
                    "BUY"
                    if pos.type == mt5.POSITION_TYPE_BUY
                    else "SELL"
                )

                logging.info(
                    f"🎯 TRAILING EXIT | "
                    f"{tipo} | "
                    f"Ticket={ticket} | "
                    f"Atual={pos.profit:.2f} | "
                    f"Máximo={max_profit:.2f} | "
                    f"Saída={trailing_level:.2f}"
                )

                close_position(pos)

                max_profit_seen.pop(
                    ticket,
                    None
                )


# ============================================================
# 🧹 LIMPA MEMÓRIA
# ============================================================

def limpar_memoria_positions(
    positions
):

    tickets_abertos = {
        pos.ticket
        for pos in positions
    }

    tickets_memoria = list(
        max_profit_seen.keys()
    )

    for ticket in tickets_memoria:

        if ticket not in tickets_abertos:

            max_profit_seen.pop(
                ticket,
                None
            )


# ============================================================
# 💰 PROCESSAMENTO DAS POSIÇÕES
# ============================================================

def processar_posicoes(
    positions,
    buy_volume,
    sell_volume,
    close_position
):

    limpar_memoria_positions(
        positions
    )

    for pos in positions:

        # ----------------------------------------------------
        # AINDA NÃO ATINGIU PROFIT
        # ----------------------------------------------------

        if pos.profit < PROFIT:

            continue

        tipo = (
            "BUY"
            if pos.type == mt5.POSITION_TYPE_BUY
            else "SELL"
        )

        logging.info(
            f"💰 PROFIT ATINGIDO | "
            f"{tipo} | "
            f"Ticket={pos.ticket} | "
            f"Lucro={pos.profit:.2f} USD | "
            f"BUY={buy_volume:.2f} | "
            f"SELL={sell_volume:.2f}"
        )

        # ----------------------------------------------------
        # NÃO BLOQUEAMOS MAIS O FECHAMENTO POR VOLUME
        # ----------------------------------------------------
        #
        # Se atingiu PROFIT, o trailing pode assumir.
        #
        # O controle de volume será utilizado para
        # NOVAS ENTRADAS.
        # ----------------------------------------------------

        if pos.ticket not in max_profit_seen:

            max_profit_seen[
                pos.ticket
            ] = pos.profit


# ============================================================
# 📈 GRID BUY
# ============================================================

def verificar_grid_buy(
    ask,
    last_buy_price,
    buys,
    buy_volume,
    sell_volume,
    open_order
):

    # --------------------------------------------------------
    # LIMITE DE QUANTIDADE
    # --------------------------------------------------------

    if buys >= MAX_ORDERS:

        logging.info(
            f"🛡️ BUY BLOQUEADO | "
            f"Quantidade máxima atingida: {buys}"
        )

        return last_buy_price

    # --------------------------------------------------------
    # LIMITE DE VOLUME
    # --------------------------------------------------------

    if not pode_abrir_buy(
        buy_volume,
        sell_volume
    ):

        return last_buy_price

    # --------------------------------------------------------
    # PRIMEIRO BUY
    # --------------------------------------------------------

    if last_buy_price is None:

        buy_condition = True

    else:

        buy_condition = (
            abs(ask - last_buy_price)
            >= GRID_DISTANCE
        )

    # --------------------------------------------------------
    # ABERTURA
    # --------------------------------------------------------

    if buy_condition:

        result = open_order(
            mt5.ORDER_TYPE_BUY
        )

        if result:

            logging.info(
                f"🟢 GRID BUY aberto | "
                f"Preço={ask:.2f} | "
                f"BUYVol antes={buy_volume:.2f}"
            )

            return ask

    return last_buy_price


# ============================================================
# 📉 GRID SELL
# ============================================================

def verificar_grid_sell(
    bid,
    last_sell_price,
    sells,
    buy_volume,
    sell_volume,
    open_order
):

    # --------------------------------------------------------
    # LIMITE DE QUANTIDADE
    # --------------------------------------------------------

    if sells >= MAX_ORDERS:

        logging.info(
            f"🛡️ SELL BLOQUEADO | "
            f"Quantidade máxima atingida: {sells}"
        )

        return last_sell_price

    # --------------------------------------------------------
    # LIMITE DE VOLUME
    # --------------------------------------------------------

    if not pode_abrir_sell(
        buy_volume,
        sell_volume
    ):

        return last_sell_price

    # --------------------------------------------------------
    # PRIMEIRO SELL
    # --------------------------------------------------------

    if last_sell_price is None:

        sell_condition = True

    else:

        sell_condition = (
            abs(bid - last_sell_price)
            >= GRID_DISTANCE
        )

    # --------------------------------------------------------
    # ABERTURA
    # --------------------------------------------------------

    if sell_condition:

        result = open_order(
            mt5.ORDER_TYPE_SELL
        )

        if result:

            logging.info(
                f"🔴 GRID SELL aberto | "
                f"Preço={bid:.2f} | "
                f"SELLVol antes={sell_volume:.2f}"
            )

            return bid

    return last_sell_price


# ============================================================
# 🎯 META GLOBAL
# ============================================================

def verificar_meta_global(
    equity,
    initial_balance
):

    profit_total = (
        equity
        - initial_balance
    )

    if profit_total >= TARGET_USD:

        logging.info(
            f"🎯 META GLOBAL ATINGIDA | "
            f"Lucro={profit_total:.2f} USD | "
            f"Meta={TARGET_USD:.2f} USD"
        )

        return True, profit_total

    return False, profit_total