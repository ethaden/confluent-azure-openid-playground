# A playground for using Azure OIDC with Confluent Cloud with Python >=3.8

## Precondition

Please set up Azure and Confluent Cloud as described in the main README.md file.

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
poetry install --no-root
```

For installing only the packages required to run the tool, use:

```bash
poetry install --without dev --no-root
```

### Configuration file

In the python folder, copy the file `example-config.yaml` to `config.yaml` and set the appropriate values.

### Authenticate to Azure

Before running the code, you need to authenticate to Azure. There are multiple ways to do that. If you use VS Code, you can install the extension `Azure Account` and authenticate directly in VS Code using the command by calling `Azure: Sign in to Azure Cloud`. Alternatively, install the `az` command line tool and run `az login`.

### Runing the code

In general, the code can be run with poetry like this:

```bash
poetry run python <src-file> [<arg>]
```

Alternatively, you can open a `poetry shell` and run `python` from there:

```bash
poetry shell
```

### Examples

List all organizations by running

```bash
poetry run python src/ccloud_list_environments.py --config config.yaml
```

## License

Copyright Eike Thaden, 2023.

See LICENSE file
