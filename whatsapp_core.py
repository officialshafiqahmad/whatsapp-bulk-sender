from __future__ import annotations

import base64
import json
import os
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


def get_session_dir(base_dir: Path | None = None) -> Path:
    if os.environ.get("SPACE_ID"):
        return Path("/data/whatsapp-session")
    if base_dir:
        return base_dir
    return Path(DEFAULT_SESSION_DIR)


def is_whatsapp_logged_in(page: Page) -> bool:
    chat_selector = 'div[contenteditable="true"][data-tab="3"], div[contenteditable="true"][data-tab="10"]'
    try:
        page.locator(chat_selector).first.wait_for(state="visible", timeout=1500)
        return True
    except PlaywrightTimeout:
        return False


def capture_qr_image(page: Page) -> str | None:
    selectors = [
        'canvas[aria-label="Scan this QR code to link a device!"]',
        'canvas[aria-label*="QR"]',
        'div[data-ref] canvas',
    ]
    for selector in selectors:
        loc = page.locator(selector)
        if loc.count() > 0:
            try:
                if loc.first.is_visible():
                    png = loc.first.screenshot(type="png")
                    return base64.b64encode(png).decode("ascii")
            except Exception:
                continue
    return None


def wait_for_whatsapp_ready(page: Page, on_status: ProgressCallback | None = None, timeout_ms: int = 300_000) -> None:
    if on_status:
        on_status({"type": "status", "message": "Opening WhatsApp Web..."})
    open_whatsapp_home(page)
    deadline = time.time() + (timeout_ms / 1000)

    while time.time() < deadline:
        if is_whatsapp_logged_in(page):
            if on_status:
                on_status({"type": "status", "message": "WhatsApp Web is ready."})
            return

        qr_image = capture_qr_image(page)
        if qr_image and on_status:
            on_status({
                "type": "qr",
                "message": "Scan this QR code with WhatsApp on your phone (Linked Devices).",
                "image": qr_image,
            })
        elif on_status:
            on_status({"type": "status", "message": "Waiting for WhatsApp login..."})

        time.sleep(2)

    raise TimeoutError("WhatsApp login timed out. Scan the QR code and try again.")


def chromium_launch_args() -> list[str]:
    args = ["--disable-blink-features=AutomationControlled"]
    if os.environ.get("SPACE_ID") or os.environ.get("HEADLESS") == "true":
        args.extend([
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ])
    return args


def launch_browser_context(playwright, session_dir: Path, headless: bool):
    return playwright.chromium.launch_persistent_context(
        user_data_dir=str(session_dir.resolve()),
        headless=headless,
        args=chromium_launch_args(),
        viewport={"width": 1280, "height": 900},
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        locale="en-US",
    )


def open_whatsapp_home(page: Page) -> None:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            page.goto(
                "https://web.whatsapp.com/",
                wait_until="commit",
                timeout=90_000,
            )
            page.wait_for_load_state("domcontentloaded", timeout=30_000)
            return
        except Exception as exc:
            last_error = exc
            time.sleep(3 * attempt)
    raise TimeoutError(f"Could not open WhatsApp Web after 3 attempts: {last_error}")


def verify_whatsapp_connectivity() -> dict:
    session_dir = get_session_dir()
    session_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = launch_browser_context(playwright, session_dir, headless=True)
        page = context.pages[0] if context.pages else context.new_page()
        open_whatsapp_home(page)
        logged_in = is_whatsapp_logged_in(page)
        qr_image = None if logged_in else capture_qr_image(page)
        context.close()
    result = {"status": "ok", "logged_in": logged_in}
    if qr_image:
        result["qr_available"] = True
    return result


def verify_browser_launch() -> dict:
    session_dir = get_session_dir()
    session_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = launch_browser_context(playwright, session_dir, headless=True)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("about:blank", wait_until="domcontentloaded", timeout=30_000)
        title = page.title()
        context.close()
    return {"status": "ok", "title": title}


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
    page.goto(url, wait_until="commit", timeout=90_000)
    page.wait_for_load_state("domcontentloaded", timeout=30_000)

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

    session_dir = session_dir or get_session_dir()
    session_dir.mkdir(parents=True, exist_ok=True)
    results: list[SendResult] = []
    total = len(contacts)

    def emit(event: dict) -> None:
        if on_progress:
            on_progress(event)

    with sync_playwright() as p:
        context = launch_browser_context(p, session_dir, headless=headless)
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
