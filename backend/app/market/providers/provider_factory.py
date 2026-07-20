from app.market.providers.kite_provider import kite_provider


class ProviderFactory:

    def __init__(self):

        self.provider = kite_provider

    def get_provider(self):

        return self.provider

    def set_provider(self, provider):

        self.provider = provider


provider_factory = ProviderFactory()