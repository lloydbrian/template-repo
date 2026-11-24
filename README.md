# template-sample-app

A sample FastAPI service built on the team Python scaffold: **mise + uv + ruff + mypy + pytest + pre-commit**, container-first with **Podman**, Python **3.14**.

Workstation prerequisites are in [`template-repo-files/template-python-projects/README.md`](https://github.com/lloydbrian/template-repo-files/blob/main/template-python-projects/README.md).

## Quick start
```bash
mise trust && mise install            # Python 3.14 from .mise.toml
mise run bootstrap                    # .venv, uv.lock, deps, pre-commit hooks
cp .env.example .env.dev              # fill values locally; never commit
uv run template-sample-app serve --reload
curl -s localhost:8000/health
```

## Tasks

| Task | What it does |
|---|---|
| `mise run bootstrap` | Create `.venv`, lock if needed, install deps and pre-commit hooks (once per clone) |
| `mise run format` | Format with ruff |
| `mise run lint` | Lint with ruff (fails on issues) |
| `mise run type` | Type-check with mypy (strict) |
| `mise run test` | Tests with coverage (fails under 80%) |
| `mise run security` | `pip-audit` + `bandit` (fails on findings) |
| `mise run image` | Build the production image with Podman |
| `mise run scan` | Scan the image with trivy (fails on HIGH/CRITICAL) |
| `mise run ci` | Exactly what CI runs: locked sync, all hooks, types, tests |

## Daily loop
| When | Run |
|---|---|
| Start of day / after pull | `uv sync` |
| While coding | `mise run lint`, `mise run test` (format runs on save and on commit) |
| Before push | `mise run ci` |
| New dependency | `uv add <pkg>` (runtime) or `uv add --group dev <pkg>` (tooling); commit `uv.lock` |
| Before release | `mise run security`, `mise run image`, `mise run scan` |

## Layout

```text
.
├── .container/            Containerfile (dev/test/prod) + compose.yaml
├── .devcontainer/         VS Code dev container (Podman)
├── .github/workflows/     ci.yml runs `mise run ci`
├── .vscode/settings.json  per-repo interpreter pin + format on save
├── .containerignore  .env.example  .gitignore  .pre-commit-config.yaml
├── .mise.toml             Python 3.14 pin, env, tasks
├── pyproject.toml  uv.lock  README.md
├── src/template_sample_app/
│   ├── main.py            FastAPI app: / and /health
│   ├── config.py          loads .env.<APP_ENV>
│   └── cli.py             typer CLI: version, serve
└── tests/
```

## Environment files and secrets

- `.env.example` is committed and lists variable **names** only.
- Copy it to `.env.dev`, `.env.test` or `.env.prod` and fill values locally. All `.env*` files except the example are git-ignored.
- `APP_ENV` picks the file at startup; real environment variables always win over file values.
- Production values belong in the platform's secret store (or `podman secret`), not in files.

## Containers (Podman)

One multi-stage `.container/Containerfile` with three targets:

| Target | Use |
|---|---|
| `dev` | Tooling included; your source is bind-mounted over `/app` |
| `test` | Copies `tests/` and runs them: the build fails if tests fail |
| `prod` | Runtime only, non-root |

```bash
podman build -f .container/Containerfile --target test .
podman build -f .container/Containerfile --target prod -t template-sample-app:0.1.0 .
mise run scan
podman compose -f .container/compose.yaml up
```

Secrets go in at run time, never into the image:
```bash
printf '%s' "$SOME_API_KEY" | podman secret create some_api_key -
podman run --secret some_api_key,type=env,target=SOME_API_KEY ...
```

The virtual environment inside images lives at `/opt/venv` (`UV_PROJECT_ENVIRONMENT`), so a mounted source folder never hides or clashes with it. Rootless notes: use host ports of 1024 or higher; add `:Z` to bind mounts on SELinux hosts.

## Conventions
- Commit messages: `feat:`, `fix:`, `chore:`, `test:`, `docs:`, `refactor:`, `ci:`.
- `GET /health` returns status, service, version and a UTC timestamp.
- Every bug fix ships with a test that failed before the fix.

## What changed in this alignment (and why)

| Before | Problem | Now |
|---|---|---|
| `.gitignore` covered `.env` only | `.env.dev`, `.env.test`, `.env.prod` could be committed | `.env.*` ignored, `.env.example` committed |
| Dev tools in `[project.optional-dependencies].dev` | `uv sync --dev` did not install them | `[dependency-groups]`: plain `uv sync` installs `dev` |
| Python 3.14 (mise), 3.12 (Docker), 3.11 (ruff, mypy, requires-python) | Passing locally, failing in the container, or the reverse | 3.14 everywhere |
| Entry point and mypy targeted a missing `ai_agent` package | Broken CLI and type check | Real package name everywhere |
| `pip-audit \|\| true` | Security task could never fail | Fails on findings; CI-ready |
| Docker files in `.docker/` | Team moved to Podman | `.container/Containerfile` (dev/test/prod) + `compose.yaml` |
| Duplicate `.mise.toml` / `.mise-python.toml` | Two sources of truth | `.mise.toml` only (Node and Java variants kept for polyglot repos) |
| No tests, CI, `.env.example`, `.containerignore` | Gates promised but not wired | All present and passing |
