from __future__ import annotations

import json
import re
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout, sync_playwright

WHATSAPP_SEND_URL = "https://web.whatsapp.com/send/"
DEFAULT_DELAY = 5
DEFAULT_SESSION_DIR = ".whatsapp-session"

ProgressCallback = Callable[[dict], None]


@dataclass
class Contact:
    name: str
    phone: str


@dataclass
class SendResult:
    contact: Contact
    success: bool
    detail: str


def normalize_phone(phone: str) -> str:
    cleaned = re.sub(r"[\s\-()]", "", str(phone).strip())
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    if not cleaned.isdigit():
        raise ValueError(f"Invalid phone number: {phone}")
    if len(cleaned) < 8 or len(cleaned) > 15:
        raise ValueError(f"Phone number must be 8–15 digits: {phone}")
    return cleaned


def parse_phone_list(text: str) -> list[Contact]:
    contacts: list[Contact] = []
    seen: set[str] = set()
    for line in re.split(r"[\n,;]+", text):
        raw = line.strip()
        if not raw:
            continue
        phone = normalize_phone(raw)
        if phone in seen:
            continue
        seen.add(phone)
        contacts.append(Contact(name=phone, phone=phone))
    return contacts


def load_config(config_path: Path | None) -> dict:
    defaults = {
        "delay_seconds": DEFAULT_DELAY,
        "headless": os.environ.get("HEADLESS", "").lower() == "true",
        "session_dir": DEFAULT_SESSION_DIR,
    }
    if config_path and config_path.exists():
        with config_path.open(encoding="utf-8") as f:
            defaults.update(json.load(f))
    return defaults


def wait_for_whatsapp_ready(page: Page, on_status: ProgressCallback | None = None, timeout_ms: int = 120_000) -> None:
    page.goto("https://web.whatsapp.com/", wait_until="domcontentloaded")
    if on_status:
        on_status({"type": "status", "message": "Scan the QR code in the browser if you are not logged in yet."})
    page.wait_for_selector(
        'div[contenteditable="true"][data-tab="3"], div[contenteditable="true"][data-tab="10"]',
        timeout=timeout_ms,
    )
    if on_status:
        on_status({"type": "status", "message": "WhatsApp Web is ready."})


def build_send_url(phone: str, message: str) -> str:
    params = urllib.parse.urlencode({"phone": phone, "text": message})
    return f"{WHATSAPP_SEND_URL}?{params}"


def dismiss_invalid_number_popup(page: Page) -> bool:
    invalid = page.locator('div[data-animate-modal-popup="true"]')
    if invalid.count() > 0 and invalid.first.is_visible():
        ok_btn = page.get_by_role("button", name=re.compile(r"OK|ok", re.I))
        if ok_btn.count() > 0:
            ok_btn.first.click()
        return True
    return False


def click_send(page: Page) -> bool:
    selectors = [
        'button[aria-label="Send"]',
        'span[data-icon="send"]',
        'div[role="button"][aria-label="Send"]',
    ]
    for selector in selectors:
        loc = page.locator(selector)
        if loc.count() > 0:
            try:
                loc.first.click(timeout=3000)
                return True
            except PlaywrightTimeout:
                continue

    message_box = page.locator('div[contenteditable="true"][data-tab="10"]')
    if message_box.count() > 0:
        message_box.first.press("Enter")
        return True
    return False


def send_to_contact(page: Page, contact: Contact, message: str) -> tuple[bool, str]:
    url = build_send_url(contact.phone, message)
    page.goto(url, wait_until="domcontentloaded")

    try:
        page.wait_for_selector(
            'div[contenteditable="true"][data-tab="10"]',
            timeout=30_000,
        )
    except PlaywrightTimeout:
        if dismiss_invalid_number_popup(page):
            return False, "Invalid phone number"
        return False, "Chat did not load in time"

    time.sleep(1.5)

    if dismiss_invalid_number_popup(page):
        return False, "Invalid phone number"

    if not click_send(page):
        return False, "Could not find send button"

    time.sleep(1)
    return True, "Sent"


def send_bulk_messages(
    contacts: list[Contact],
    message: str,
    *,
    delay_seconds: int = DEFAULT_DELAY,
    headless: bool = False,
    session_dir: Path | None = None,
    on_progress: ProgressCallback | None = None,
) -> list[SendResult]:
    if not contacts:
        raise ValueError("No contacts to send to.")

    session_dir = session_dir or Path(DEFAULT_SESSION_DIR)
    session_dir.mkdir(parents=True, exist_ok=True)
    results: list[SendResult] = []
    total = len(contacts)

    def emit(event: dict) -> None:
        if on_progress:
            on_progress(event)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir.resolve()),
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 900},
        )
        page = context.pages[0] if context.pages else context.new_page()

        wait_for_whatsapp_ready(page, on_status=emit)

        for index, contact in enumerate(contacts, 1):
            emit({
                "type": "progress",
                "current": index,
                "total": total,
                "phone": contact.phone,
                "message": f"Sending to {contact.phone}...",
            })

            ok, detail = send_to_contact(page, contact, message)
            results.append(SendResult(contact=contact, success=ok, detail=detail))

            emit({
                "type": "result",
                "current": index,
                "total": total,
                "phone": contact.phone,
                "success": ok,
                "detail": detail,
            })

            if index < total:
                time.sleep(delay_seconds)

        context.close()

    sent = sum(1 for r in results if r.success)
    emit({
        "type": "complete",
        "sent": sent,
        "failed": len(results) - sent,
        "total": total,
    })
    return results
