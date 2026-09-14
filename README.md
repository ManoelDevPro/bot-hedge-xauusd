# 🤖 Bot Hedge XAUUSD

Robô de trading automatizado desenvolvido em **Python** para operar o **XAUUSD (Ouro)** através do **MetaTrader 5**.

O projeto utiliza uma estratégia baseada em **Hedge + Grid**, buscando trabalhar o equilíbrio entre posições de compra (BUY) e venda (SELL), combinando gerenciamento de volume, trailing de lucro e uma meta global de resultado.

> ⚠️ **Aviso:** este projeto possui finalidade experimental e educacional. Não existe garantia de lucro. Trading envolve riscos e o código deve ser testado cuidadosamente em conta demo antes de qualquer utilização em conta real.

---

## 📌 Sobre o projeto

O Bot Hedge XAUUSD foi desenvolvido para automatizar uma estratégia de negociação no MetaTrader 5.

A estrutura do projeto foi separada em módulos para facilitar a manutenção e evolução do sistema:

- `hedge_bot.py` → execução principal e comunicação com o MetaTrader 5
- `estrategia.py` → regras e lógica da estratégia
- `config_volume.py` → configurações da estratégia e conexão
- `.env` → credenciais e configurações sensíveis do MetaTrader 5

---

## ⚙️ Estratégia

O robô utiliza uma abordagem baseada em:

### 🔹 Hedge

O sistema trabalha inicialmente com posições:

```text
BUY + SELL
