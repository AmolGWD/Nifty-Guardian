"""
RuntimeEngine: drives a `MarketDataSource` through `EventProcessor`,
one candle at a time, via a `Scheduler` - the one place this package
ties orchestration, replay pacing, and session state together. No
business logic lives here; every actual decision is `EventProcessor`
delegating into the existing (frozen) pipeline.
"""

from app.market_data.schemas import Candle
from app.runtime.engine_config import EngineConfig, sleep_seconds_for
from app.runtime.event_processor import EventProcessor
from app.runtime.health import HealthMonitor
from app.runtime.market_data_source import MarketDataSource
from app.runtime.scheduler import Scheduler
from app.runtime.session_controller import SessionController, SessionState

_DEFAULT_CANDLE_INTERVAL_SECONDS = 15 * 60  # 15-minute candles, this platform's own convention


class RuntimeEngine:
    def __init__(
        self,
        *,
        config: EngineConfig,
        market_data_source: MarketDataSource,
        event_processor: EventProcessor,
        session_controller: SessionController,
        scheduler: Scheduler,
        health_monitor: HealthMonitor,
        candle_interval_seconds: float = _DEFAULT_CANDLE_INTERVAL_SECONDS,
    ) -> None:
        self._config = config
        self._market_data_source = market_data_source
        self._event_processor = event_processor
        self._session_controller = session_controller
        self._scheduler = scheduler
        self._health_monitor = health_monitor
        self._candle_interval_seconds = candle_interval_seconds

        self._history: list[Candle] = []
        self._remaining_candles = iter(market_data_source)
        self._processed_count = 0

    def run(self) -> None:
        """
        Drives candles through the scheduler until the session pauses,
        stops, ends, or the data source is exhausted - then returns
        control to the caller. Calling `run()` again after `resume()`
        continues from exactly where it left off (the candle iterator
        and history are held on `self`, not local to one `run()` call)
        - this is what makes Pause/Resume meaningful for a fully
        synchronous, single-threaded engine: there is no other thread
        that could call `pause()` *during* a blocking `run()`, so
        pausing only ever takes effect between `run()` invocations.
        """
        state = self._session_controller.state
        if state == SessionState.NOT_STARTED:
            self._session_controller.start()
        elif state == SessionState.PAUSED:
            self._session_controller.resume()
        elif state in (SessionState.STOPPED, SessionState.ENDED):
            return  # nothing to do - call replay() for a fresh run, not run() again

        delay = sleep_seconds_for(self._candle_interval_seconds, self._config.replay_speed)
        self._scheduler.run(self._step, delay_seconds=delay)

    def _step(self) -> bool:
        if self._session_controller.state != SessionState.RUNNING:
            return False

        if (
            self._config.maximum_candles is not None
            and self._processed_count >= self._config.maximum_candles
        ):
            return self._maybe_auto_stop()

        try:
            candle = next(self._remaining_candles)
        except StopIteration:
            return self._maybe_auto_stop()

        self._history.append(candle)
        latency = self._event_processor.process_candle(candle, self._history)
        self._health_monitor.record_candle_processed(latency)
        self._processed_count += 1
        return True

    def _maybe_auto_stop(self) -> bool:
        if self._config.auto_stop_on_completion:
            self._session_controller.stop()
        return False

    @property
    def processed_count(self) -> int:
        return self._processed_count

    @property
    def session_controller(self) -> SessionController:
        return self._session_controller
