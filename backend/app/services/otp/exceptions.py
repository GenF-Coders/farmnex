from __future__ import annotations


class OTPError(Exception):
    pass


class OTPNotFoundError(OTPError):
    pass


class OTPExpiredError(OTPError):
    pass


class OTPAlreadyVerifiedError(OTPError):
    pass


class OTPMaxAttemptsExceededError(OTPError):
    pass


class OTPInvalidError(OTPError):
    pass


class OTPResendCooldownError(OTPError):
    pass


class OTPResendLimitExceededError(OTPError):
    pass


class OTPProviderError(OTPError):
    pass


class OTPProviderTimeoutError(OTPProviderError):
    pass


class OTPProviderUnavailableError(OTPProviderError):
    pass


class OTPProviderRateLimitError(OTPProviderError):
    pass