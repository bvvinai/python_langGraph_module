from __future__ import annotations


class AppError(Exception):
    def __init__(self, message: str, code: str = "app_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ProviderNotFoundError(AppError):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Provider '{provider}' was not found.", code="provider_not_found")


class ProviderAuthError(AppError):
    def __init__(self, provider: str) -> None:
        super().__init__(f"Provider '{provider}' is missing authentication.", code="provider_auth_error")


class ProviderRequestError(AppError):
    def __init__(self, provider: str, message: str) -> None:
        super().__init__(f"Provider '{provider}' request failed: {message}", code="provider_request_error")
