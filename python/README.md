# A playground for using Azure OIDC with Confluent Cloud with Python >=3.8

## Development

### Installing `poetry`

This project uses `poetry`. You can install `poetry` by following the instructions on the poetry website https://python-poetry.org/.

If you want virtual environments to be created by poetry in general in `.venv` within your python folder (recommeded for development with VS Code), run:

```bash
poetry config --local virtualenvs.in-project true
```

### Install all packages with poetry

For development including tools for generating documentation, use:

```bash
poetry install
```

For installing only the packages required to run the tool, use:

```bash
poetry install --without dev
```

### Runing the code

```bash
poetry run python <src-file> [<arg>]
```

Alternatively, you can open a `poetry shell` and run `python` from there:

```bash
poetry shell
```

## License

Copyright Eike Thaden, 2023.

See LICENSE file
