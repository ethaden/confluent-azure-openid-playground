# Base class for providing authentication headers or tokens for clients
from abc import ABC
from typing import Dict

class CCloud_Auth_Provider_Base(ABC):
    def get_bearer(self, uri: str) -> str:
        pass

    def get_auth_header(self, uri: str) -> Dict[str, str]:
        pass

class AuthenticationError(Exception):
    pass
