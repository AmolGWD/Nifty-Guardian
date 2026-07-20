from abc import ABC, abstractmethod


class BaseMarketProvider(ABC):

    @abstractmethod
    def get_market_data(self):
        """
        Returns current market data.
        """
        pass