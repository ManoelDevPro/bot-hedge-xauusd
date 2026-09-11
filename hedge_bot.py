import MetaTrader5 as mt5
import time
import logging

from config_volume import (
    SYMBOL,
    LOT,
    MT5_LOGIN,
    MT5_PASSWORD,
    MT5_SERVER,
    MT5_PATH
)

# ============================================================
# 🧠 IMPORTA A ESTRATÉGIA
# ============================================================

from estrategia import (
    processar_trailing,
    processar_posicoes,
    verificar_grid_buy,
    verificar_grid_sell,
    verificar_meta_global
)


# ============================================================
# 📝 LOG
# ============================================================

logging.basicConfig(
    filename="hedge_bot.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# 🚀 INICIALIZA MT5
# ============================================================

if MT5_PATH:

    init = mt5.initialize(
        path=MT5_PATH,
        login=MT5_LOGIN,
        password=MT5_PASSWORD,
        server=MT5_SERVER
    )

else:

    init = mt5.initialize(
        login=MT5_LOGIN,
        password=MT5_PASSWORD,
        server=MT5_SERVER
    )


if not init:

    logging.error(
        f"❌ Falha ao inicializar MT5: "
        f"{mt5.last_error()}"
    )

    quit()


# ============================================================
# 🔥 ATIVA SÍMBOLO
# ============================================================

if not mt5.symbol_select(
    SYMBOL,
    True
):

    logging.error(
        f"❌ Falha ao selecionar {SYMBOL}"
    )

    mt5.shutdown()

    quit()


# ============================================================
# 💰 BANCA INICIAL
# ============================================================

account_info = mt5.account_info()

if account_info is None:

    logging.error(
        f"❌ Falha ao pegar conta: "
        f"{mt5.last_error()}"
    )

    mt5.shutdown()

    quit()


initial_balance = (
    account_info.balance
)


logging.info(
    f"✅ Robô iniciado | "
    f"Banca inicial: {initial_balance:.2f} USD | "
    f"Lote: {LOT}"
)


# ============================================================
# 📍 CONTROLE GRID
# ============================================================

last_buy_price = None
last_sell_price = None


# ============================================================
# 💰 PREÇO
# ============================================================

def get_price():

    tick = mt5.symbol_info_tick(
        SYMBOL
    )

    if tick is None:

        return None, None

    return tick.ask, tick.bid


# ============================================================
# 🟢 ABRIR ORDEM
# ============================================================

def open_order(order_type):

    ask, bid = get_price()

    if ask is None:

        logging.error(
            "❌ Falha ao obter preço"
        )

        return None


    price = (
        ask
        if order_type == mt5.ORDER_TYPE_BUY
        else bid
    )


    tipo = (
        "BUY"
        if order_type == mt5.ORDER_TYPE_BUY
        else "SELL"
    )


    filling_modes = [

        mt5.ORDER_FILLING_RETURN,

        mt5.ORDER_FILLING_IOC,

        mt5.ORDER_FILLING_FOK

    ]


    for mode in filling_modes:

        request = {

            "action":
                mt5.TRADE_ACTION_DEAL,

            "symbol":
                SYMBOL,

            "volume":
                LOT,

            "type":
                order_type,

            "price":
                price,

            "deviation":
                10,

            "magic":
                123456,

            "comment":
                "hedge_bot",

            "type_time":
                mt5.ORDER_TIME_GTC,

            "type_filling":
                mode,
        }


        result = mt5.order_send(
            request
        )


        if result is None:

            logging.error(
                f"❌ Sem retorno MT5 | "
                f"{tipo}"
            )

            continue


        if (
            result.retcode
            == mt5.TRADE_RETCODE_DONE
        ):

            logging.info(
                f"✅ Ordem executada {tipo} | "
                f"Preço: {price} | "
                f"Lote: {LOT} | "
                f"Ticket: {result.order}"
            )

            return result


        logging.warning(
            f"⚠️ Falha {tipo} | "
            f"Retcode: {result.retcode} | "
            f"Mode: {mode}"
        )


    logging.error(
        f"❌ Nenhum filling funcionou | "
        f"{tipo}"
    )

    return None


# ============================================================
# 🔴 FECHAR POSIÇÃO
# ============================================================

def close_position(position):

    ask, bid = get_price()

    if ask is None:

        logging.error(
            "❌ Falha ao obter preço para fechar"
        )

        return


    order_type = (

        mt5.ORDER_TYPE_SELL
        if position.type == mt5.POSITION_TYPE_BUY
        else mt5.ORDER_TYPE_BUY

    )


    price = (

        bid
        if order_type == mt5.ORDER_TYPE_SELL
        else ask

    )


    tipo = (

        "BUY"
        if position.type == mt5.POSITION_TYPE_BUY
        else "SELL"

    )


    filling_modes = [

        mt5.ORDER_FILLING_RETURN,

        mt5.ORDER_FILLING_IOC,

        mt5.ORDER_FILLING_FOK

    ]


    for mode in filling_modes:

        request = {

            "action":
                mt5.TRADE_ACTION_DEAL,

            "symbol":
                SYMBOL,

            "volume":
                position.volume,

            "type":
                order_type,

            "position":
                position.ticket,

            "price":
                price,

            "deviation":
                10,

            "magic":
                123456,

            "comment":
                "close",

            "type_time":
                mt5.ORDER_TIME_GTC,

            "type_filling":
                mode,

        }


        result = mt5.order_send(
            request
        )


        if result is None:

            continue


        if (
            result.retcode
            == mt5.TRADE_RETCODE_DONE
        ):

            logging.info(
                f"💰 Ordem fechada {tipo} | "
                f"Lucro: {position.profit:.2f} USD | "
                f"Ticket: {position.ticket}"
            )

            return


        logging.warning(
            f"⚠️ Falha ao fechar "
            f"{position.ticket} | "
            f"Retcode: {result.retcode}"
        )


    logging.error(
        f"❌ Falha ao fechar posição "
        f"{position.ticket}"
    )


# ============================================================
# 📊 POSIÇÕES
# ============================================================

def get_positions():

    return mt5.positions_get(
        symbol=SYMBOL
    )


# ============================================================
# 💰 EQUITY
# ============================================================

def get_equity():

    account = mt5.account_info()

    return (
        account.equity
        if account
        else 0
    )


# ============================================================
# 📊 CONTAGEM
# ============================================================

def count_positions():

    positions = get_positions()

    if positions is None:

        return 0, 0


    buys = len([

        p for p in positions
        if p.type == mt5.POSITION_TYPE_BUY

    ])


    sells = len([

        p for p in positions
        if p.type == mt5.POSITION_TYPE_SELL

    ])


    return buys, sells


# ============================================================
# ⚖️ VOLUME TOTAL BUY × SELL
# ============================================================

def get_total_volume():

    positions = get_positions()

    if positions is None:

        return 0.0, 0.0


    buy_volume = sum(

        p.volume
        for p in positions
        if p.type == mt5.POSITION_TYPE_BUY

    )


    sell_volume = sum(

        p.volume
        for p in positions
        if p.type == mt5.POSITION_TYPE_SELL

    )


    return buy_volume, sell_volume


# ============================================================
# 🔥 MERCADO ABERTO
# ============================================================

def mercado_aberto():

    info = mt5.symbol_info(
        SYMBOL
    )

    if info is None:

        return False


    return (
        info.trade_mode
        == mt5.SYMBOL_TRADE_MODE_FULL
    )


# ============================================================
# 🚀 LOOP PRINCIPAL
# ============================================================

meta_batida = False


try:

    while True:

        try:

            # ------------------------------------------------
            # MERCADO
            # ------------------------------------------------

            if not mercado_aberto():

                logging.info(
                    "⛔ Mercado fechado..."
                )

                time.sleep(60)

                continue


            # ------------------------------------------------
            # PREÇOS
            # ------------------------------------------------

            ask, bid = get_price()

            if ask is None:

                time.sleep(5)

                continue


            # ------------------------------------------------
            # DADOS
            # ------------------------------------------------

            positions = get_positions()

            equity = get_equity()


            # =================================================
            # 1️⃣ HEDGE INICIAL
            # =================================================

            if (
                positions is None
                or len(positions) == 0
            ):

                logging.info(
                    "🔄 Abrindo hedge inicial..."
                )


                buy_result = open_order(
                    mt5.ORDER_TYPE_BUY
                )


                sell_result = open_order(
                    mt5.ORDER_TYPE_SELL
                )


                if buy_result:

                    last_buy_price = ask


                if sell_result:

                    last_sell_price = bid


                time.sleep(5)

                continue


            # =================================================
            # 2️⃣ CONTAGEM
            # =================================================

            buys, sells = (
                count_positions()
            )


            # =================================================
            # 3️⃣ VOLUME TOTAL
            # =================================================

            buy_volume, sell_volume = (
                get_total_volume()
            )


            logging.info(
                f"⚖️ Volume | "
                f"BUY={buy_volume:.2f} | "
                f"SELL={sell_volume:.2f}"
            )


            # =================================================
            # 4️⃣ FECHAMENTO POR PROFIT + VOLUME
            # =================================================

            processar_posicoes(

                positions,

                buy_volume,

                sell_volume,

                close_position

            )


            # =================================================
            # 5️⃣ TRAILING PROFIT
            # =================================================

            positions = get_positions()

            if positions:

                processar_trailing(

                    positions,

                    close_position

                )


            # =================================================
            # 6️⃣ GRID BUY
            # =================================================

            last_buy_price = (
                verificar_grid_buy(

                    ask,

                    last_buy_price,

                    buys,

                    open_order

                )
            )


            # =================================================
            # 7️⃣ GRID SELL
            # =================================================

            last_sell_price = (
                verificar_grid_sell(

                    bid,

                    last_sell_price,

                    sells,

                    open_order

                )
            )


            # =================================================
            # 8️⃣ META GLOBAL
            # =================================================

            atingiu_meta, profit_total = (
                verificar_meta_global(

                    equity,

                    initial_balance

                )
            )


            if (
                atingiu_meta
                and not meta_batida
            ):

                meta_batida = True


                positions = get_positions()


                if positions:

                    logging.info(
                        "🔒 Fechando todas "
                        "as posições..."
                    )


                    for pos in positions:

                        close_position(
                            pos
                        )


                time.sleep(20)


                account_info = (
                    mt5.account_info()
                )


                if account_info:

                    initial_balance = (
                        account_info.balance
                    )


                logging.info(
                    f"🔄 Novo ciclo iniciado | "
                    f"Nova banca base: "
                    f"{initial_balance:.2f} USD"
                )


                meta_batida = False

                continue


            # =================================================
            # 9️⃣ LOOP
            # =================================================

            time.sleep(2)


        except Exception as e:

            logging.error(
                f"❌ Erro no loop: {e}"
            )

            time.sleep(5)


finally:

    mt5.shutdown()

    logging.info(
        "🔌 MT5 desconectado com segurança"
    )