"""Command-line entry point: `uv run template-sample-app --help`."""

from __future__ import annotations

from importlib.metadata import version as pkg_version

import typer

app = typer.Typer(help="Template Sample App tools", no_args_is_help=True)


@app.command()
def version() -> None:
    """Print the installed package version."""
    typer.echo(pkg_version("template-sample-app"))


@app.command()
def config() -> None:
    """Validate settings and print them (fails fast on invalid configuration)."""
    from template_sample_app.config import get_settings

    typer.echo(get_settings().model_dump_json(indent=2))


@app.command()
def serve(host: str = "127.0.0.1", port: int | None = None, reload: bool = False) -> None:
    """Run the API locally with uvicorn."""
    import uvicorn

    from template_sample_app.config import get_settings

    uvicorn.run(
        "template_sample_app.main:app",
        host=host,
        port=port or get_settings().http_port,
        reload=reload,
    )
