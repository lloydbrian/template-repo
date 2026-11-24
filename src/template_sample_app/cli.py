"""Command-line entry point: `uv run template-sample-app --help`."""

from __future__ import annotations

from importlib.metadata import version as pkg_version

import typer

app = typer.Typer(help="Sample app tools", no_args_is_help=True)


@app.command()
def version() -> None:
    """Print the installed package version."""
    typer.echo(pkg_version("template-sample-app"))


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Run the API locally with uvicorn."""
    import uvicorn

    uvicorn.run("template_sample_app.main:app", host=host, port=port, reload=reload)
