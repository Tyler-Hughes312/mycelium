"""Privacy policy enforcement hooks (FR-19 / AD-2).

Call these before any future remote upload or remote LLM site.
"""

from __future__ import annotations

from mycelium.core.config import MyceliumConfig, NetworkPolicy


class PrivacyError(RuntimeError):
    """Raised when a remote action is blocked by local policy."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def assert_allow_code_upload(policy: NetworkPolicy | MyceliumConfig) -> None:
    """Raise PrivacyError unless allow_code_upload is enabled."""
    net = policy.network if isinstance(policy, MyceliumConfig) else policy
    if not net.allow_code_upload:
        raise PrivacyError(
            "code_upload_disabled",
            "Remote code/vault upload is disabled. Enable allow_code_upload in Settings.",
        )


def assert_allow_remote_llm(policy: NetworkPolicy | MyceliumConfig) -> None:
    """Raise PrivacyError unless allow_remote_llm is enabled."""
    net = policy.network if isinstance(policy, MyceliumConfig) else policy
    if not net.allow_remote_llm:
        raise PrivacyError(
            "remote_llm_disabled",
            "Remote LLM calls are disabled. Enable allow_remote_llm in Settings.",
        )
