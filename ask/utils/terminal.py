# from rich.console import Console

# console = Console()


# def print_error(message: str):
#     console.print(f"[bold red]Error:[/bold red] {message}")


# def print_info(message: str):
#     console.print(f"[cyan]{message}[/cyan]")


from rich.console import Console
from rich.markdown import Markdown

console = Console()


def render_response(response: str):
    console.print()
    console.print(Markdown(response, code_theme="monokai"))
    console.print()


def print_error(message: str):
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_info(message: str):
    console.print(f"[bold cyan]INFO:[/bold cyan] {message}")


def print_success(message: str):
    console.print(f"[bold green]SUCCESS:[/bold green] {message}")
