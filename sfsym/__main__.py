#!/usr/bin/env python3

from itertools import filterfalse
import json
import plistlib
import typer
from rich.console import Console
from pathlib import Path
from typing import Iterable, Iterator

console = Console()
error_console = Console(stderr=True)

app = typer.Typer(help="SF Symbols JSON Generator CLI")


def ignore_lines(lines: Iterable[str]) -> Iterator[str]:
    def should_ignore(line: str) -> bool:
        if line.lstrip().startswith("//"):
            return True
        if line.strip() == "":
            return True
        return False

    return filterfalse(should_ignore, lines)


def read_aliases(symbols: dict[str, str], aliases_path: Path) -> dict[str, str]:
    with aliases_path.open("rb") as f:
        return plistlib.load(f)


def add_aliases(symbols: dict[str, str], aliases: dict[str, str]) -> int:
    warnings = 0
    for alias, symbol_name in aliases.items():
        try:
            symbols[alias] = symbols[symbol_name]
        except KeyError:
            warnings += 1
            error_console.print(
                f"[bold yellow]WARNING:[/bold yellow] Alias {alias} points to non-existing symbol name {symbol_name}",
            )
    return warnings


@app.command()
def generate(
    source: Path = typer.Option(
        help="Path to SF Symbols definitions", default=Path("./source")
    ),
    target: Path = typer.Option(
        help="Path to output JSON file",
        default=Path("./sf-symbols-unicode-mappings.json"),
    ),
    escape_unicode: bool = typer.Option(
        help="Escape Unicode characters", default=False
    ),
    include_aliases: bool = typer.Option(help="Include aliases", default=False),
    include_legacy_aliases: bool = typer.Option(
        help="Include legacy aliases", default=False
    ),
):
    """Generate JSON from SF Symbols definitions."""
    console.print("[bold green]Generating SF Symbols JSON...[/bold green]")

    if not source.exists():
        console.print(f"[bold red]Source path does not exist: {source}[/bold red]")
        raise typer.Exit(1)

    symbols_file = source / "symbol_previews.txt"
    with symbols_file.open() as f:
        symbol_chars = next(ignore_lines(f)).strip()

    names_file = source / "symbol_names.txt"
    symbols = {}
    with names_file.open() as names:
        for name, symbol in zip(ignore_lines(names), symbol_chars):
            symbols[name.strip()] = symbol

    aliases_count = 0
    warnings = 0
    if include_aliases:
        aliases = read_aliases(symbols, source / "name_aliases.strings")
        warnings += add_aliases(symbols, aliases)
        aliases_count += len(aliases)

    if include_legacy_aliases:
        aliases = read_aliases(symbols, source / "legacy_aliases.strings")
        warnings += add_aliases(symbols, aliases)
        aliases_count += len(aliases)

    with target.open("w") as f:
        json.dump(symbols, f, indent=4, ensure_ascii=escape_unicode)

    console.print(f"[bold green]Generated [cyan]{len(symbols)}[/cyan] symbols and [cyan]{aliases_count}[/cyan] aliases[/bold green]")
    console.print(f"[bold yellow]Found [cyan]{warnings}[/cyan] warnings[/bold yellow]")
    console.print(f"[bold green]Saved to {target}[/bold green]")


@app.command()
def search():
    """Search for a symbol by name."""
    error_console.print("[red]Symbol search is not implemented yet[/red]")
    raise typer.Exit(1)


def main():
    app()


if __name__ == "__main__":
    main()
