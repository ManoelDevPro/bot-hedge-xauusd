import MetaTrader5 as mt5
import logging


# ============================================================
# MEMÓRIA DO TRAILING
# ============================================================

max_profit_seen = {}


# ============================================================
# CONFIGURAÇÃO DO TRAILING
# ============================================================

PROFIT = 12.0
TRAILING_PERCENT = 0.50


# ============================================================
# TRAILING PROFIT
# ============================================================

def processar_trailing(positions, close_position):
    """
    Controla o trailing individual de cada posição.

    Quando a posição atinge o lucro mínimo definido em PROFIT,
    começa a acompanhar o maior lucro observado.

    Exemplo:
        PROFIT = 12
        TRAILING_PERCENT = 0.50

        Máximo atingido = 20 USD
        Nível de saída = 10 USD

        Se o lucro cair para <= 10 USD,
        a posição será fechada.
    """

    for position in positions:

        ticket = position.ticket
        current_profit = position.profit

        # Primeira vez que vemos esta posição
        if ticket not in max_profit_seen:
            max_profit_seen[ticket] = current_profit

        # Atualiza maior lucro
        if current_profit > max_profit_seen[ticket]:
            max_profit_seen[ticket] = current_profit

        max_profit = max_profit_seen[ticket]

        # Só ativa trailing depois do lucro mínimo
        if max_profit >= PROFIT:

            trailing_level = max_profit * TRAILING_PERCENT

            logging.info(
                f"📈 Trailing | "
                f"Ticket={ticket} | "
                f"Atual={current_profit:.2f} | "
                f"Máximo={max_profit:.2f} | "
                f"Saída={trailing_level:.2f}"
            )

            # Aciona fechamento
            if current_profit <= trailing_level:

                logging.info(
                    f"🔴 Trailing acionado | "
                    f"Ticket={ticket} | "
                    f"Lucro={current_profit:.2f}"
                )

                close_position(position)


# ============================================================
# LIMPAR MEMÓRIA DO TRAILING
# ============================================================

def limpar_memoria_positions(positions):

    tickets_abertos = {
        position.ticket
        for position in positions
    }

    for ticket in list(max_profit_seen.keys()):

        if ticket not in tickets_abertos:

            del max_profit_seen[ticket]


# ============================================================
# PROCESSAMENTO DAS POSIÇÕES
# ============================================================

def processar_posicoes(
    positions,
    buy_volume,
    sell_volume,
    close_position
):
    """
    Apenas registra as posições.

    O fechamento individual fica por conta
    do trailing.

    O limite de volume NÃO impede fechamento.
    Ele serve somente para controlar novas entradas.
    """

    if not positions:
        return

    for position in positions:

        tipo = (
            "BUY"
            if position.type == mt5.POSITION_TYPE_BUY
            else "SELL"
        )

        logging.info(
            f"📊 Posição | "
            f"Ticket={position.ticket} | "
            f"Tipo={tipo} | "
            f"Volume={position.volume:.2f} | "
            f"Profit={position.profit:.2f}"
        )


# ============================================================
# NET VOLUME
# ============================================================

def calcular_net_volume(
    buy_volume,
    sell_volume
):
    return buy_volume - sell_volume


# ============================================================
# PODE ABRIR BUY?
# ============================================================

def pode_abrir_buy(
    buy_volume,
    sell_volume,
    lot,
    max_buy_volume,
    max_net_volume
):

    novo_buy_volume = buy_volume + lot

    novo_net_volume = (
        novo_buy_volume - sell_volume
    )

    # Limite total BUY
    if novo_buy_volume > max_buy_volume:

        logging.info(
            f"⛔ BUY bloqueado | "
            f"BUY após entrada={novo_buy_volume:.2f} | "
            f"Máximo={max_buy_volume:.2f}"
        )

        return False

    # Limite de exposição líquida
    if novo_net_volume > max_net_volume:

        logging.info(
            f"⛔ BUY bloqueado | "
            f"NET após entrada={novo_net_volume:.2f} | "
            f"Máximo={max_net_volume:.2f}"
        )

        return False

    return True


# ============================================================
# PODE ABRIR SELL?
# ============================================================

def pode_abrir_sell(
    buy_volume,
    sell_volume,
    lot,
    max_sell_volume,
    max_net_volume
):

    novo_sell_volume = sell_volume + lot

    novo_net_volume = (
        buy_volume - novo_sell_volume
    )

    # Limite total SELL
    if novo_sell_volume > max_sell_volume:

        logging.info(
            f"⛔ SELL bloqueado | "
            f"SELL após entrada={novo_sell_volume:.2f} | "
            f"Máximo={max_sell_volume:.2f}"
        )

        return False

    # Limite de exposição líquida
    if novo_net_volume < -max_net_volume:

        logging.info(
            f"⛔ SELL bloqueado | "
            f"NET após entrada={novo_net_volume:.2f} | "
            f"Mínimo={-max_net_volume:.2f}"
        )

        return False

    return True


# ============================================================
# GRID BUY
# ============================================================

def verificar_grid_buy(
    ask,
    last_buy_price,
    buys,
    buy_volume,
    sell_volume,
    open_order,
    lot,
    grid_distance,
    max_orders,
    max_buy_volume,
    max_net_volume
):

    # Ainda não existe referência
    if last_buy_price is None:
        return last_buy_price

    # Limite de quantidade de BUY
    if buys >= max_orders:

        logging.info(
            f"⛔ MAX_ORDERS BUY atingido | "
            f"BUY={buys}"
        )

        return last_buy_price

    # Distância desde último BUY
    distancia = last_buy_price - ask

    # Só abre BUY se o preço caiu a distância configurada
    if distancia >= grid_distance:

        # Verifica exposição
        if not pode_abrir_buy(
            buy_volume,
            sell_volume,
            lot,
            max_buy_volume,
            max_net_volume
        ):
            return last_buy_price

        # Abre BUY
        result = open_order(
            mt5.ORDER_TYPE_BUY
        )

        if result:

            logging.info(
                f"🟢 GRID BUY | "
                f"Preço={ask:.2f} | "
                f"Distância={distancia:.2f}"
            )

            return ask

    return last_buy_price


# ============================================================
# GRID SELL
# ============================================================

def verificar_grid_sell(
    bid,
    last_sell_price,
    sells,
    buy_volume,
    sell_volume,
    open_order,
    lot,
    grid_distance,
    max_orders,
    max_sell_volume,
    max_net_volume
):

    # Ainda não existe referência
    if last_sell_price is None:
        return last_sell_price

    # Limite de quantidade de SELL
    if sells >= max_orders:

        logging.info(
            f"⛔ MAX_ORDERS SELL atingido | "
            f"SELL={sells}"
        )

        return last_sell_price

    # Distância desde último SELL
    distancia = bid - last_sell_price

    # Só abre SELL se o preço subiu a distância configurada
    if distancia >= grid_distance:

        # Verifica exposição
        if not pode_abrir_sell(
            buy_volume,
            sell_volume,
            lot,
            max_sell_volume,
            max_net_volume
        ):
            return last_sell_price

        # Abre SELL
        result = open_order(
            mt5.ORDER_TYPE_SELL
        )

        if result:

            logging.info(
                f"🔴 GRID SELL | "
                f"Preço={bid:.2f} | "
                f"Distância={distancia:.2f}"
            )

            return bid

    return last_sell_price


# ============================================================
# META GLOBAL
# ============================================================

def verificar_meta_global(
    equity,
    initial_balance,
    target_usd
):

    profit_total = (
        equity - initial_balance
    )

    if profit_total >= target_usd:

        logging.info(
            f"🎯 META GLOBAL ATINGIDA | "
            f"Equity={equity:.2f} | "
            f"Banca base={initial_balance:.2f} | "
            f"Lucro={profit_total:.2f}"
        )

        return True, profit_total

    return False, profit_total