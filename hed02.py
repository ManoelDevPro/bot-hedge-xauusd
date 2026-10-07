import MetaTrader5 as mt5
import time
import logging


# ============================================================
# CONFIGURAÇÕES
# ============================================================

from config02  import (
    SYMBOL,
    LOT,
    GRID_DISTANCE,
    TARGET_USD,
    MAX_ORDERS,
    MAX_BUY_VOLUME,
    MAX_SELL_VOLUME,
    MAX_NET_VOLUME,
    MT5_LOGIN,
    MT5_PASSWORD,
    MT5_SERVER,
    MT5_PATH
)


# ============================================================
# ESTRATÉGIA
# ============================================================

from estrategia import (
    processar_trailing,
    processar_posicoes,
    verificar_grid_buy,
    verificar_grid_sell,
    verificar_meta_global,
    limpar_memoria_positions
)


# ============================================================
# LOG
# ============================================================

logging.basicConfig(
    filename="hedge_bot.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# INICIALIZA MT5
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
# ATIVA SÍMBOLO
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
# BANCA INICIAL
# ============================================================

account_info = mt5.account_info()


if account_info is None:

    logging.error(
        f"❌ Falha ao pegar conta: "
        f"{mt5.last_error()}"
    )

    mt5.shutdown()

    quit()


initial_balance = account_info.balance


logging.info(
    f"✅ Robô iniciado | "
    f"Banca inicial: {initial_balance:.2f} USD | "
    f"Lote: {LOT} | "
    f"Grid: {GRID_DISTANCE} | "
    f"Meta: {TARGET_USD:.2f}"
)


# ============================================================
# CONTROLE DO GRID
# ============================================================

last_buy_price = None
last_sell_price = None


# ============================================================
# OBTER PREÇO
# ============================================================

def get_price():

    tick = mt5.symbol_info_tick(
        SYMBOL
    )

    if tick is None:

        return None, None

    return tick.ask, tick.bid


# ============================================================
# ABRIR ORDEM
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
                mode

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


        if result.retcode == mt5.TRADE_RETCODE_DONE:

            logging.info(
                f"✅ Ordem executada {tipo} | "
                f"Preço={price} | "
                f"Lote={LOT} | "
                f"Ticket={result.order}"
            )

            return result


        logging.warning(
            f"⚠️ Falha {tipo} | "
            f"Retcode={result.retcode} | "
            f"Mode={mode}"
        )


    logging.error(
        f"❌ Nenhum filling funcionou | "
        f"{tipo}"
    )


    return None


# ============================================================
# FECHAR POSIÇÃO
# ============================================================

def close_position(position):

    ask, bid = get_price()


    if ask is None:

        logging.error(
            "❌ Falha ao obter preço para fechar"
        )

        return False


    # BUY fecha com SELL
    # SELL fecha com BUY

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
                "close_all",

            "type_time":
                mt5.ORDER_TIME_GTC,

            "type_filling":
                mode

        }


        result = mt5.order_send(
            request
        )


        if result is None:

            continue


        if result.retcode == mt5.TRADE_RETCODE_DONE:

            logging.info(
                f"💰 Ordem fechada {tipo} | "
                f"Lucro={position.profit:.2f} USD | "
                f"Ticket={position.ticket}"
            )

            return True


        logging.warning(
            f"⚠️ Falha ao fechar "
            f"Ticket={position.ticket} | "
            f"Retcode={result.retcode} | "
            f"Mode={mode}"
        )


    logging.error(
        f"❌ Falha ao fechar posição "
        f"{position.ticket}"
    )


    return False


# ============================================================
# OBTER POSIÇÕES
# ============================================================

def get_positions():

    return mt5.positions_get(
        symbol=SYMBOL
    )


# ============================================================
# OBTER EQUITY
# ============================================================

def get_equity():

    account = mt5.account_info()


    if account:

        return account.equity


    return 0.0


# ============================================================
# CONTAR POSIÇÕES
# ============================================================

def count_positions():

    positions = get_positions()


    if positions is None:

        return 0, 0


    buys = len([

        p
        for p in positions

        if p.type == mt5.POSITION_TYPE_BUY

    ])


    sells = len([

        p
        for p in positions

        if p.type == mt5.POSITION_TYPE_SELL

    ])


    return buys, sells


# ============================================================
# VOLUME TOTAL
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
# MERCADO ABERTO
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
# FECHAR TODAS AS POSIÇÕES
# ============================================================

def fechar_todas_posicoes(
    timeout=30
):

    """
    Fecha todas as posições e NÃO retorna
    sucesso até confirmar que existem
    zero posições abertas.
    """

    inicio = time.time()


    logging.info(
        "🔒 INICIANDO FECHAMENTO TOTAL..."
    )


    while (
        time.time() - inicio
        < timeout
    ):

        positions = get_positions()


        # Erro na consulta
        if positions is None:

            logging.error(
                f"❌ Erro ao consultar posições | "
                f"{mt5.last_error()}"
            )

            time.sleep(1)

            continue


        # ====================================================
        # ZERO POSIÇÕES = CICLO FECHADO
        # ====================================================

        if len(positions) == 0:

            logging.info(
                "✅ FECHAMENTO TOTAL CONFIRMADO | "
                "0 posições abertas."
            )

            return True


        logging.info(
            f"🔒 Ainda existem "
            f"{len(positions)} posição(ões). "
            f"Fechando..."
        )


        # Tenta fechar todas
        for position in positions:

            close_position(
                position
            )


        # Dá tempo para MT5 processar
        time.sleep(1)


    # ========================================================
    # ÚLTIMA CONFERÊNCIA
    # ========================================================

    positions = get_positions()


    if (
        positions is not None
        and len(positions) == 0
    ):

        logging.info(
            "✅ FECHAMENTO TOTAL CONFIRMADO."
        )

        return True


    logging.error(
        "❌ NÃO FOI POSSÍVEL CONFIRMAR "
        "O FECHAMENTO DE TODAS AS POSIÇÕES."
    )


    return False


# ============================================================
# LOOP PRINCIPAL
# ============================================================

try:

    while True:

        try:

            # =================================================
            # MERCADO
            # =================================================

            if not mercado_aberto():

                logging.info(
                    "⛔ Mercado fechado..."
                )

                time.sleep(60)

                continue


            # =================================================
            # PREÇOS
            # =================================================

            ask, bid = get_price()


            if ask is None:

                time.sleep(5)

                continue


            # =================================================
            # DADOS ATUAIS
            # =================================================

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


                time.sleep(0.5)


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
            # 3️⃣ VOLUME
            # =================================================

            buy_volume, sell_volume = (
                get_total_volume()
            )


            logging.info(
                f"⚖️ Volume | "
                f"BUY={buy_volume:.2f} | "
                f"SELL={sell_volume:.2f} | "
                f"NET="
                f"{buy_volume - sell_volume:.2f}"
            )


            # =================================================
            # 4️⃣ PROCESSAMENTO DAS POSIÇÕES
            # =================================================

            processar_posicoes(

                positions,

                buy_volume,

                sell_volume,

                close_position

            )


            # =================================================
            # 5️⃣ TRAILING
            # =================================================

            positions = get_positions()


            if positions:

                processar_trailing(

                    positions,

                    close_position

                )


            # =================================================
            # LIMPA MEMÓRIA DO TRAILING
            # =================================================

            positions_after_trailing = (
                get_positions()
            )


            if positions_after_trailing is not None:

                limpar_memoria_positions(
                    positions_after_trailing
                )


            # =================================================
            # 6️⃣ ATUALIZA EQUITY
            # =================================================

            equity = get_equity()


            # =================================================
            # 7️⃣ VERIFICA META GLOBAL
            # =================================================

            atingiu_meta, profit_total = (
                verificar_meta_global(

                    equity,

                    initial_balance,

                    TARGET_USD

                )
            )


            logging.info(
                f"💰 CICLO | "
                f"Banca Base={initial_balance:.2f} | "
                f"Equity={equity:.2f} | "
                f"Resultado={profit_total:.2f} | "
                f"Meta={TARGET_USD:.2f}"
            )


            # =================================================
            # 🎯 META ATINGIDA
            # =================================================

            if atingiu_meta:

                logging.info(
                    f"🎯 META ATINGIDA | "
                    f"Lucro do ciclo="
                    f"{profit_total:.2f} USD"
                )


                # =================================================
                # IMPORTANTE:
                #
                # NÃO abre GRID.
                #
                # Primeiro fecha tudo.
                # =================================================

                sucesso = (
                    fechar_todas_posicoes(
                        timeout=30
                    )
                )


                # =================================================
                # SE NÃO CONSEGUIU FECHAR TUDO
                # =================================================

                if not sucesso:

                    logging.error(
                        "⚠️ META ATINGIDA, PORÉM "
                        "AINDA EXISTEM POSIÇÕES."
                    )

                    logging.error(
                        "⚠️ NOVO CICLO NÃO SERÁ "
                        "INICIADO ATÉ ZERAR AS POSIÇÕES."
                    )


                    time.sleep(5)

                    continue


                # =================================================
                # PEQUENA ESPERA PARA ATUALIZAR CONTA
                # =================================================

                time.sleep(2)


                account_info = (
                    mt5.account_info()
                )


                if account_info is None:

                    logging.error(
                        "❌ Não foi possível "
                        "atualizar a conta."
                    )


                    time.sleep(5)

                    continue


                # =================================================
                # NOVA BANCA BASE
                # =================================================

                initial_balance = (
                    account_info.balance
                )


                # =================================================
                # REINICIA REFERÊNCIAS DO GRID
                # =================================================

                last_buy_price = None

                last_sell_price = None


                # =================================================
                # LOG NOVO CICLO
                # =================================================

                logging.info(
                    f"🔄 NOVO CICLO INICIADO | "
                    f"Nova banca base="
                    f"{initial_balance:.2f} USD | "
                    f"Próxima meta="
                    f"{initial_balance + TARGET_USD:.2f} USD"
                )


                time.sleep(3)


                # Volta para o início.
                # Como não existem posições,
                # o hedge inicial será aberto.
                continue


            # =================================================
            # 8️⃣ GRID BUY
            # =================================================

            # Atualiza tudo novamente antes do BUY

            positions = get_positions()

            buys, sells = (
                count_positions()
            )

            buy_volume, sell_volume = (
                get_total_volume()
            )


            last_buy_price = (
                verificar_grid_buy(

                    ask,

                    last_buy_price,

                    buys,

                    buy_volume,

                    sell_volume,

                    open_order,

                    LOT,

                    GRID_DISTANCE,

                    MAX_ORDERS,

                    MAX_BUY_VOLUME,

                    MAX_NET_VOLUME

                )
            )


            # =================================================
            # 9️⃣ GRID SELL
            # =================================================

            # O BUY acima pode ter aberto uma nova posição.
            # Portanto recalculamos os volumes.

            positions = get_positions()

            buys, sells = (
                count_positions()
            )

            buy_volume, sell_volume = (
                get_total_volume()
            )


            last_sell_price = (
                verificar_grid_sell(

                    bid,

                    last_sell_price,

                    sells,

                    buy_volume,

                    sell_volume,

                    open_order,

                    LOT,

                    GRID_DISTANCE,

                    MAX_ORDERS,

                    MAX_SELL_VOLUME,

                    MAX_NET_VOLUME

                )
            )


            # =================================================
            # 🔟 LOOP
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