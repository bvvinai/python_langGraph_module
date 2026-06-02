from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppError(Exception):
    message: str
    code: str = "app_error"
    status_code: int = 400

    def __str__(self) -> str:
        return self.message


class ProviderNotFoundError(AppError):
    def __init__(self, provider: str) -> None:
        super().__init__(
            message=f"Provider '{provider}' is not registered.",
            code="provider_not_found",
            status_code=404,
        )


class ProviderDisabledError(AppError):
    def __init__(self, provider: str) -> None:
        super().__init__(
            message=f"Provider '{provider}' is disabled by configuration.",
            code="provider_disabled",
            status_code=400,
        )


class ProviderConfigurationError(AppError):
    def __init__(self, provider: str, reason: str) -> None:
        super().__init__(
            message=f"Provider '{provider}' is not configured: {reason}",
            code="provider_not_configured",
            status_code=500,
        )


class FeatureDisabledError(AppError):
    def __init__(self, feature: str) -> None:
        super().__init__(
            message=f"Feature '{feature}' is disabled.",
            code="feature_disabled",
            status_code=400,
        )


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code="validation_error",
            status_code=422,
        )
