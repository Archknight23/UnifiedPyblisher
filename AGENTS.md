# Repository Guidelines

## Project Structure & Module Organization
- `publisherlogic/` holds the PyQt6 backend (entry point: `publisherlogic/main.py`, integrations in `publisherlogic/api_bluesky.py`, credential storage in `publisherlogic/credentials.py`).
- `index.html` is the frontend UI loaded by the Qt web view (Tailwind CDN + custom CSS/JS).
- `requirements.txt` lists Python dependencies for the desktop app.
- `start_linux.sh`, `start_mac.command`, and `start_windows.bat` are the cross-platform launchers.
- `venv/` is a local virtual environment created by the launchers (not meant for version control).

## Build, Test, and Development Commands
- `./start_linux.sh` (Linux), `./start_mac.command` (macOS), or `start_windows.bat` (Windows): create/activate `venv`, install deps, then run the app.
- `python -m unittest` runs the lightweight unit tests in `tests/`.
- Manual run:
  - `python -m venv venv`
  - `source venv/bin/activate` (or `venv\\Scripts\\activate` on Windows)
  - `pip install -r requirements.txt`
  - `python -m publisherlogic.main`

## Coding Style & Naming Conventions
- Python: 4-space indentation, PEP 8-style naming (`ClassName`, `snake_case`), short docstrings on public methods.
- HTML/CSS/JS: keep formatting consistent with `index.html` (4-space indents, double-quoted attributes, Tailwind utility classes).
- No formatter or linter is configured; avoid large reformat-only diffs.

## Testing Guidelines
- Unit tests live in `tests/` and use Python's built-in `unittest` framework.
- Also validate changes by launching the app and exercising the UI flow (login, queue, publish).

## Commit & Pull Request Guidelines
- Commit messages in history are short, descriptive sentences (no strict conventional commit format). Keep them one line and specific.
- PRs should include: a brief summary, manual test steps, and screenshots or screen recordings for UI changes.

## Security & Configuration Tips
- Credentials are stored locally in `~/.unifiedpublisher/` and encrypted by `publisherlogic/credentials.py`.
- Use app passwords for third-party services; never commit secrets or exported credential files.
