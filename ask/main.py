import argparse
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from ask.core.chat import ask_once, ask_stream
from ask.core.config import config_path, load_config, save_config
from ask.core.history import History
from ask.utils.terminal import (
    print_error,
    print_info,
    render_response,
)

# Typer is used for named commands. A small dispatcher below handles the
# default `ask "question"` form without confusing questions with subcommands.
cli = typer.Typer(
    name="ask",
    help="Talk to AI models directly from your terminal.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()
SUBCOMMANDS = {"setup", "models", "history", "chat"}


def resolve_provider(model: str, provider: Optional[str] = None) -> str:
    """Resolve a provider from an explicit provider or a recognizable model ID."""
    if provider:
        return provider.strip().lower()

    value = (model or "").strip().lower()

    if value in {"gemini", "google"} or value.startswith("gemini-"):
        return "gemini"

    if value == "groq" or value.startswith(
        ("llama-", "mixtral-", "gemma-", "qwen/", "deepseek-r1-distill-")
    ):
        return "groq"

    if value in {"openai", "gpt"} or value.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"

    return "openai"


def default_model(provider: str, cfg: dict) -> str:
    provider = (provider or "openai").strip().lower()
    model_settings = {
        "openai": ("openai_model", "gpt-4.1-mini"),
        "gemini": ("gemini_model", "gemini-3.8-flash"),
        "groq": ("groq_model", "llama-3.3-70b-versatile"),
    }
    setting, fallback = model_settings.get(provider, model_settings["openai"])
    return cfg.get(setting) or fallback


def execute_prompt(
    prompt: Optional[str],
    model: Optional[str],
    provider: Optional[str],
    file: Optional[Path],
    no_stream: bool,
) -> None:
    cfg = load_config()

    if file is not None:
        if not file.exists() or not file.is_file():
            print_error(f"File does not exist or is not a regular file: {file}")
            raise typer.Exit(1)

        try:
            file_text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            print_error(f"Could not read file: {exc}")
            raise typer.Exit(1)

        prompt = (
            (prompt or "Explain this file")
            + f"\n\n--- FILE: {file.name} ---\n"
            + file_text
        )

    if not prompt or not prompt.strip():
        print_error('Provide a prompt, e.g. ask "Explain Linux processes".')
        raise typer.Exit(2)

    selected_provider = (provider or cfg.get("default_provider") or "openai").lower()

    if model:
        model_alias = model.strip().lower()
        if model_alias in {"openai", "gpt", "gemini", "google", "groq"}:
            selected_provider = resolve_provider(model_alias, provider)
            selected_model = default_model(selected_provider, cfg)
        else:
            selected_model = model
            selected_provider = resolve_provider(model, provider)
    else:
        selected_model = default_model(selected_provider, cfg)

    try:
        if no_stream:
            answer = ask_once(prompt, selected_provider, selected_model, cfg)
        else:
            chunks = []
            for chunk in ask_stream(prompt, selected_provider, selected_model, cfg):
                chunks.append(chunk)

            answer = "".join(chunks)

        render_response(answer or "")

        History().add(prompt, answer, selected_provider, selected_model)

    except Exception as exc:
        print_error(str(exc))
        raise typer.Exit(1)


def print_root_help() -> None:
    console.print(
        Panel(
            "[bold cyan]ASK CLI[/bold cyan]\n"
            "A unified AI client for your terminal.\n\n"
            "[bold]Ask a question:[/bold]\n"
            '  ask "Explain Linux processes"\n'
            '  ask -p groq "Explain Linux processes"\n'
            '  ask -p gemini -f notes.txt "Summarize this file"\n\n'
            "[bold]Commands:[/bold]\n"
            "  ask setup       Configure API keys and default models\n"
            "  ask chat        Start an interactive chat\n"
            "  ask models      Show configured models\n"
            "  ask history     Show recent conversations\n\n"
            "[bold]Prompt options:[/bold]\n"
            "  -p, --provider  openai, gemini, or groq\n"
            "  -m, --model     Provider alias or specific model ID\n"
            "  -f, --file      Include a UTF-8 text file\n"
            "  --no-stream     Print the complete response at once\n",
            title="Usage",
            border_style="cyan",
        )
    )


def run_prompt_cli(args: list[str]) -> None:
    """Parse the default prompt invocation, e.g. `ask -p groq "hello"`."""
    parser = argparse.ArgumentParser(
        prog="ask",
        description="Ask an AI model directly from your terminal.",
    )
    parser.add_argument("-p", "--provider", help="openai, gemini, or groq")
    parser.add_argument("-m", "--model", help="Provider alias or specific model ID")
    parser.add_argument("-f", "--file", type=Path, help="Include a UTF-8 text file")
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Print the complete response at once",
    )
    parser.add_argument("prompt", nargs="*", help="Your question or instruction")

    parsed = parser.parse_args(args)
    prompt = " ".join(parsed.prompt).strip() if parsed.prompt else None

    execute_prompt(
        prompt=prompt,
        model=parsed.model,
        provider=parsed.provider,
        file=parsed.file,
        no_stream=parsed.no_stream,
    )


@cli.command()
def setup() -> None:
    """Configure API keys and default models."""
    cfg = load_config()

    console.print(Panel.fit("[bold cyan]ASK CLI Setup[/bold cyan]"))
    console.print(f"Configuration file: {config_path()}")

    key_fields = [
        ("openai_api_key", "OpenAI"),
        ("gemini_api_key", "Gemini"),
        ("groq_api_key", "Groq"),
    ]

    for key, label in key_fields:
        entered = Prompt.ask(
            f"{label} API key (press Enter to keep the saved key)",
            password=True,
            default="",
        )
        if entered.strip():
            cfg[key] = entered.strip()

    cfg["default_provider"] = Prompt.ask(
        "Default provider",
        choices=["openai", "gemini", "groq"],
        default=cfg.get("default_provider", "openai"),
    )

    cfg["openai_model"] = Prompt.ask(
        "OpenAI model",
        default=cfg.get("openai_model", "gpt-4.1-mini"),
    )
    cfg["gemini_model"] = Prompt.ask(
        "Gemini model",
        default=cfg.get("gemini_model", "gemini-3.8-flash"),
    )
    cfg["groq_model"] = Prompt.ask(
        "Groq model",
        default=cfg.get("groq_model", "llama-3.3-70b-versatile"),
    )

    save_config(cfg)
    print_info("Configuration saved successfully.")


@cli.command()
def models() -> None:
    """Show configured providers and default models."""
    cfg = load_config()
    console.print(
        Panel(
            f"[bold]Default provider:[/bold] {cfg.get('default_provider', 'openai')}\n"
            f"[bold]OpenAI:[/bold] {cfg.get('openai_model', 'gpt-4.1-mini')}\n"
            f"[bold]Gemini:[/bold] {cfg.get('gemini_model', 'gemini-3.8-flash')}\n"
            f"[bold]Groq:[/bold] {cfg.get('groq_model', 'llama-3.3-70b-versatile')}",
            title="ASK Models",
            border_style="cyan",
        )
    )


@cli.command()
def history(
    limit: int = typer.Option(
        20, min=1, max=200, help="Number of recent conversations to show"
    )
) -> None:
    """Show recent conversations."""
    entries = History().recent(limit)

    if not entries:
        print_info("No saved conversations.")
        return

    for item in entries:
        console.print(
            Panel(
                f"[bold cyan]You:[/bold cyan] {item['prompt']}\n\n"
                f"[bold green]ASK ({item['provider']} / {item['model']}):[/bold green]\n"
                f"{item['response']}",
                border_style="dim",
            )
        )


@cli.command()
def chat(
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Provider alias or model ID"
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="openai, gemini, or groq"
    ),
) -> None:
    """Start an interactive chat session."""
    cfg = load_config()
    selected_provider = (provider or cfg.get("default_provider") or "openai").lower()

    if model and model.strip().lower() in {"openai", "gpt", "gemini", "google", "groq"}:
        selected_provider = resolve_provider(model, provider)
        selected_model = default_model(selected_provider, cfg)
    else:
        selected_model = model or default_model(selected_provider, cfg)
        selected_provider = resolve_provider(selected_model, selected_provider)

    console.print(
        Panel.fit(
            "[bold cyan]ASK Interactive Chat[/bold cyan]\n"
            f"Provider: {selected_provider}\n"
            f"Model: {selected_model}\n"
            "[dim]/exit to quit | /clear to reset context[/dim]",
            border_style="cyan",
        )
    )

    messages: list[dict[str, str]] = []

    while True:
        try:
            prompt = Prompt.ask("[bold cyan]You[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Chat ended.[/dim]")
            break

        command = prompt.strip().lower()
        if command in {"/exit", "/quit"}:
            break
        if command == "/clear":
            messages.clear()
            print_info("Conversation context cleared.")
            continue
        if not prompt.strip():
            continue

        messages.append({"role": "user", "content": prompt})

        try:
            response_parts = []

            for chunk in ask_stream(
                prompt,
                selected_provider,
                selected_model,
                cfg,
                messages[:-1],
            ):
                response_parts.append(chunk)

            answer = "".join(response_parts)

            console.print("[bold green]ASK[/bold green]")
            render_response(answer)
            messages.append({"role": "assistant", "content": answer})
            History().add(prompt, answer, selected_provider, selected_model)

        except Exception as exc:
            print_error(str(exc))
            messages.pop()


def app() -> None:
    """
    Console-script entry point.

    Known first arguments are dispatched to Typer subcommands.
    All other arguments are treated as a direct AI prompt.
    """
    args = sys.argv[1:]

    if not args:
        print_root_help()
        return

    if args[0] in SUBCOMMANDS:
        cli(args=args, prog_name="ask")
        return

    if args[0] in {"--help", "-h"}:
        print_root_help()
        return

    try:
        run_prompt_cli(args)
    except typer.Exit as exc:
        raise SystemExit(exc.exit_code)


if __name__ == "__main__":
    app()
