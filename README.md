# ASK CLI

A small, extensible terminal client for OpenAI and Google Gemini.

## Features

- Ask questions directly from your shell
- Choose a provider/model (`openai` or `gemini`)
- Stream answers to the terminal
- Interactive chat mode
- Read a prompt from a file
- Keep a local SQLite conversation history
- Store API keys in `~/.config/ask-cli/config.json`

## Install (Termux / Kali NetHunter)

Install Python and build tools first:

```bash
pkg update && pkg upgrade
pkg install python git
```

On Kali NetHunter, use your package manager if Python/pip are not already installed.

Unzip this project, enter the directory, then:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install .
```

If your environment does not support virtual environments, use `pipx` if available, or install inside a virtual environment rather than forcing a system-wide pip install.

## Configure

```bash
ask setup
```

You can also set environment variables:

```bash
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
```

API access and billing are separate from ChatGPT or Google consumer subscriptions.

## Usage

```bash
ask "Explain how DNS works"
ask -m openai "Explain Linux namespaces"
ask -m gemini "Explain Linux namespaces"
ask -m gpt-4.1 "Write a Python example"
ask -m gemini-2.5-flash "Summarize this topic"
ask -f notes.txt "Summarize these notes"
ask chat
ask history
ask history --limit 10
ask models
```

Default model names can be changed in `ask/core/config.py` or supplied with `-m`.

## Notes

- `-m openai` and `-m gemini` are convenient aliases. You may also supply a specific model ID.
- The first version only sends text prompts. It does not execute shell commands.
- Keep API keys private. Do not commit your config file or `.env` file.
- To uninstall: `pip uninstall ask-cli`

## Development install

```bash
pip install -e .
```

This installs the `ask` command in editable mode, so source changes are picked up immediately.
