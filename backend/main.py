from app.config.settings import APP_NAME
from app.models.market_data import MarketData
from app.strategy.signal_engine import generate_signal
from app.utils.printer import print_signal


def main():

    # Dummy market data
    data = MarketData(
        current_price=24280,
        previous_close=24220,
        open_price=24255,
        ema=24240,
        rsi=58,
        supertrend_green=True,
        resistance=24270,
        support=24180,
        ce_oi=120000,
        pe_oi=180000,
    )

    signal = generate_signal(data)

    print_signal(signal, data)


if __name__ == "__main__":
    main()