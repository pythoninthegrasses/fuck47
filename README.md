# fuck ~~45~~ 47

When having the same conversations with friends and family goes nowhere.

## Minimum Requirements

* [python 3.14]()
* [mise]()

## Quickstart

```bash
# install deps
mise install

# sync python deps
uv sync --all-extras

# run the app
uv run main.py
```

## Development

```bash
# lint
ruff check .

# format
ruff format .

# run tests
pytest

# render index/archive from the filtered articles store
uv run python -m utils.render

# manually add an article
uv run ./cli.py add-article <url>
```
