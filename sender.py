#!/usr/bin/env python3
"""CLI wrapper for WhatsApp bulk sender."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from whatsapp_core import (
    Contact,
    load_config,
    parse_phone_list,
    send_bulk_messages,
)


def load_contacts_from_csv(path: Path) -> list[Contact]:
    import csv

    contacts: list[Contact] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "phone" not in (reader.fieldnames or []):
            raise click.ClickException(f"CSV must have a 'phone' column: {path}")
        for row in reader:
            phone = row.get("phone", "").strip()
            if not phone:
                continue
            name = row.get("name", phone).strip() or phone
            parsed = parse_phone_list(phone)[0]
            contacts.append(Contact(name=name, phone=parsed.phone))
    return contacts


@click.command()
@click.option("--list", "list_path", type=click.Path(exists=True, path_type=Path))
@click.option("--phones", help="Comma-separated phone numbers")
@click.option("--message", "-m", required=True)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=Path("config.json"))
@click.option("--delay", type=int, default=None)
@click.option("--dry-run", is_flag=True)
def main(
    list_path: Path | None,
    phones: str | None,
    message: str,
    config_path: Path,
    delay: int | None,
    dry_run: bool,
) -> None:
    if not list_path and not phones:
        raise click.ClickException("Provide --list employees.csv OR --phones 923...,923...")

    config = load_config(config_path if config_path.exists() else None)
    delay_seconds = delay if delay is not None else config.get("delay_seconds", 5)
    headless = config.get("headless", False)
    session_dir = Path(config.get("session_dir", ".whatsapp-session"))

    if list_path:
        contacts = load_contacts_from_csv(list_path)
    else:
        contacts = parse_phone_list(phones or "")

    if not contacts:
        raise click.ClickException("No contacts found.")

    click.echo(f"Contacts: {len(contacts)}")
    click.echo(f"Message: {message[:80]}{'...' if len(message) > 80 else ''}")

    if dry_run:
        for i, c in enumerate(contacts, 1):
            click.echo(f"  {i}. {c.name} ({c.phone})")
        return

    def on_progress(event: dict) -> None:
        if event.get("type") == "result":
            status = "OK" if event.get("success") else "FAILED"
            click.echo(f"  -> {status}: {event.get('phone')} ({event.get('detail')})")
        elif event.get("type") == "status":
            click.echo(event.get("message"))
        elif event.get("type") == "complete":
            click.echo(f"Done. Sent: {event.get('sent')}, Failed: {event.get('failed')}")

    results = send_bulk_messages(
        contacts,
        message,
        delay_seconds=delay_seconds,
        headless=headless,
        session_dir=session_dir,
        on_progress=on_progress,
    )

    failed = [r for r in results if not r.success]
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
