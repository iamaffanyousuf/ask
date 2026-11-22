from rich.markdown import Markdown


def markdown_response(text: str) -> Markdown:
    return Markdown(text)
