from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from .state import load_json, mark_sender_warning_shown, save_json


class DeliveryFunction(Protocol):
    def __call__(self, file_path: Path, kindle_address: str) -> None: ...


@dataclass(frozen=True)
class DeliveryResult:
    handed_to_mailer: bool
    warning: str | None = None
    send_convention: str | None = None


def deliver_to_harness(
    *,
    file_path: str | Path,
    kindle_address: str,
    preferences_path: str | Path = "preferences.local.json",
    send: DeliveryFunction | None = None,
) -> DeliveryResult:
    warning = None
    if not mark_sender_warning_shown(preferences_path):
        warning = (
            "Approve the harness sender email in Amazon Personal Document Settings "
            "before relying on Kindle delivery."
        )

    if send is None:
        return DeliveryResult(handed_to_mailer=False, warning=warning)

    path = Path(file_path)
    send(path, kindle_address)
    convention = f"deliver {path} to {kindle_address}"
    prefs = load_json(preferences_path, {})
    prefs.setdefault("send_convention", convention)
    save_json(preferences_path, prefs)
    return DeliveryResult(
        handed_to_mailer=True,
        warning=warning,
        send_convention=convention,
    )
