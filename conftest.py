from requests import Session
import pytest
import yaml

class ApiClient:
    def __init__(self) -> None:
        self._session = Session()

    def get_session(self):
        return self._session

@pytest.fixture(scope="session", autouse=True)
def load_config():
    with open('testconfig.yaml', 'r') as f:
        yml_config = yaml.safe_load(f)
    return yml_config

@pytest.fixture(scope="session", autouse=True)
def api_client():
    return ApiClient()

@pytest.fixture(scope="session", autouse=True)
def session(api_client):
    return api_client.get_session()

@pytest.fixture(scope="session")
def model():
    return "DS100"