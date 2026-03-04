from app.schemas.incident import IncidentDecision


class BaseDecisionProvider:
    def generate(self, prompt: str, fallback: IncidentDecision) -> IncidentDecision:
        raise NotImplementedError


class MockDecisionProvider(BaseDecisionProvider):
    def generate(self, prompt: str, fallback: IncidentDecision) -> IncidentDecision:
        return fallback


def get_decision_provider(provider_name: str) -> BaseDecisionProvider:
    if provider_name == "mock":
        return MockDecisionProvider()
    return MockDecisionProvider()
