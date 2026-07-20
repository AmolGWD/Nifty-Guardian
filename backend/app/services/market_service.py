from app.market.providers.provider_factory import provider_factory


class MarketService:

    def get_market_data(self):

        provider = provider_factory.get_provider()

        return provider.get_market_data()


market_service = MarketService()