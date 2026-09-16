from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.otp.schemas import (
    OTPProviderVerifyResult,
    OTPSendResult,
)


class OTPProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def send_otp(
        self,
        *,
        phone_number: str,
    ) -> OTPSendResult:
        raise NotImplementedError

    @abstractmethod
    async def verify_otp(
        self,
        *,
        phone_number: str,
        otp: str,
    ) -> OTPProviderVerifyResult:
        raise NotImplementedError