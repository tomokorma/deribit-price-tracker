from src.app.config import Config


class TestConfig(Config):
    """Test environment config."""

    FIRST_RESPONSE_VALIDATION = True
