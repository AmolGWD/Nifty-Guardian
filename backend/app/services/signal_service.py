from app.strategy.guardian_engine import guardian_engine
from app.services.signal_manager import signal_manager


class SignalService:

    def generate_signal(self, market, indicators):

        # Generate trade from Guardian Engine
        trade = guardian_engine.evaluate(
            market,
            indicators
        )

        # Apply quality filters
        trade = signal_manager.qualify(
            trade
        )

        return trade


signal_service = SignalService()