import pytest
from fake_validator import FakeValidator

@pytest.fixture
def validator():
    return FakeValidator(chaos_mode=False)

@pytest.fixture
def chaos_validator():
    return FakeValidator(chaos_mode=True, chaos_probability=0.1)
