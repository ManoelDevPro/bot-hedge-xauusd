import MetaTrader5 as mt5
import logging

from config_volume import (
    PROFIT,
    TRAILING_PERCENT,
    TARGET_USD,
    MAX_ORDERS,
    GRID_DISTANCE
)


# ============================================================
# 🧠 MEMÓRIA DA ESTRATÉGIA
# ============================================================

# Guarda o maior lucro alcançado por cada posição
max_profit_seen = {}


# ============================================================
# 🎯 TRAILING PROFIT
# ============================================================

#TRAILING_PERCENT = 0.70
# 0.70 = permite devolver no máximo 30% do lucro máximo

def processar_trailing(
    positions,
    close_position
):
    """
    Monitora o maior lucro de cada posição.

    Quando a posição atinge PROFIT:
        começa o trailing.

    Exemplo:

        Máximo = 20 USD
        Trailing = 70%

        nível de saída = 14 USD

    Se cair de 20 para 14:
        fecha.

    Se continuar subindo:
        acompanha o novo máximo.
    """

    for pos in positions:

        ticket = pos.ticket

        # ----------------------------------------------------
        # PRIMEIRA VEZ QUE ENXERGA A POSIÇÃO
        # ----------------------------------------------------

        if ticket not in max_profit_seen:
            max_profit_seen[ticket] = pos.profit

        # ----------------------------------------------------
        # ATUALIZA MAIOR LUCRO
        # ----------------------------------------------------

        if pos.profit > max_profit_seen[ticket]:
            max_profit_seen[ticket] = pos.profit

        max_profit = max_profit_seen[ticket]

        # ----------------------------------------------------
        # TRAILING SÓ ATIVA DEPOIS DO PROFIT MÍNIMO
        # ----------------------------------------------------

        if max_profit >= PROFIT:

            trailing_level = max_profit * TRAILING_PERCENT

            # ------------------------------------------------
            # DEVOLVEU 30% DO LUCRO
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
                    f"Ticket: {ticket} | "
                    f"Atual: {pos.profit:.2f} USD | "
                    f"Máximo: {max_profit:.2f} USD | "
                    f"Saída: {trailing_level:.2f} USD"
                )

                close_position(pos)

                # Remove memória da posição
                max_profit_seen.pop(ticket, None)


# ============================================================
# 🧹 LIMPA POSIÇÕES QUE JÁ NÃO EXISTEM
# ============================================================

def limpar_memoria_positions(positions):

    tickets_abertos = {
        pos.ticket for pos in positions
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
# ⚖️ CONTROLE DE VOLUME BUY × SELL
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
# 🧠 DECISÃO DE FECHAMENTO POR VOLUME
# ============================================================

def pode_fechar_posicao(
    position,
    buy_volume,
    sell_volume
):

    # --------------------------------------------------------
    # BUY
    # --------------------------------------------------------

    if position.type == mt5.POSITION_TYPE_BUY:

        # Existem muitos SELLs presos
        if sell_volume > buy_volume:

            logging.info(
                f"🧠 HOLD BUY | "
                f"BuyVol={buy_volume:.2f} | "
                f"SellVol={sell_volume:.2f}"
            )

            return False

        return True

    # --------------------------------------------------------
    # SELL
    # --------------------------------------------------------

    if position.type == mt5.POSITION_TYPE_SELL:

        # Existem muitos BUYs presos
        if buy_volume > sell_volume:

            logging.info(
                f"🧠 HOLD SELL | "
                f"BuyVol={buy_volume:.2f} | "
                f"SellVol={sell_volume:.2f}"
            )

            return False

        return True

    return True


# ============================================================
# 💰 PROCESSAMENTO DAS POSIÇÕES
# ============================================================

def processar_posicoes(
    positions,
    buy_volume,
    sell_volume,
    close_position
):

    # Primeiro limpa posições antigas da memória
    limpar_memoria_positions(
        positions
    )

    for pos in positions:

        # ----------------------------------------------------
        # POSIÇÃO AINDA NÃO ATINGIU O PROFIT
        # ----------------------------------------------------

        if pos.profit < PROFIT:

            continue

        # ----------------------------------------------------
        # ANALISA VOLUME
        # ----------------------------------------------------

        pode_fechar = pode_fechar_posicao(
            pos,
            buy_volume,
            sell_volume
        )

        if not pode_fechar:

            continue

        # ----------------------------------------------------
        # ATINGIU PROFIT E PODE FECHAR
        # ----------------------------------------------------

        tipo = (
            "BUY"
            if pos.type == mt5.POSITION_TYPE_BUY
            else "SELL"
        )

        logging.info(
            f"💰 PROFIT ATINGIDO | "
            f"{tipo} | "
            f"Ticket: {pos.ticket} | "
            f"Lucro: {pos.profit:.2f} USD"
        )

        # O trailing passa a controlar a posição
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
    open_order
):

    if buys >= MAX_ORDERS:

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

    if buy_condition:

        result = open_order(
            mt5.ORDER_TYPE_BUY
        )

        if result:

            logging.info(
                f"🟢 GRID BUY aberto | "
                f"Preço: {ask}"
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
    open_order
):

    if sells >= MAX_ORDERS:

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

    if sell_condition:

        result = open_order(
            mt5.ORDER_TYPE_SELL
        )

        if result:

            logging.info(
                f"🔴 GRID SELL aberto | "
                f"Preço: {bid}"
            )

            return bid

    return last_sell_price


# ============================================================
# 🎯 VERIFICA META GLOBAL
# ============================================================

def verificar_meta_global(
    equity,
    initial_balance
):

    profit_total = (
        equity - initial_balance
    )

    if profit_total >= TARGET_USD:

        logging.info(
            f"🎯 META GLOBAL ATINGIDA | "
            f"Lucro: {profit_total:.2f} USD | "
            f"Meta: {TARGET_USD:.2f} USD"
        )

        return True, profit_total

    return False, profit_total