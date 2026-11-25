# Plan 001: Spike foundation

- **Spec:** [spec.md](spec.md)
- **Status:** Approved

## Approach
Create a small Python 3.12 package in `pipeline/` using the `src/` layout, managed with `uv`. It has a Typer-based CLI named `evidence-mapper`, one empty module per pipeline stage, Pydantic Settings that read only from environment variables, and a logging setup that follows SP-01. A default-deny `.gitignore` rule for `data/` lets only the manifests through. Tests cover every acceptance criterion, even though tests are optional for spike code, because they're cheap here and AC-5 and AC-6 ask for them.

## Components affected
- [x] Pipeline (`pipeline/`)
- [x] Data layout (`data/`, `.gitignore`)
- [x] Docs (`README.md`, `CLAUDE.md`, `docs/architecture.md`)
- [ ] Backend, database, frontend: not in this spec (ADR 0002)
- [ ] Infrastructure (AWS): none

## Decisions taken in this plan

### CLI framework: Typer
A CLI framework reads the command line (subcommands, options, `--help`) and calls the matching Python function. Typer builds options from type hints, which matches our Pydantic and type-hints-everywhere style, and generates `--help` text without extra code. It's built on Click, so Click's features stay available if we need them. See Alternatives.

### `data/` layout (spike only)
This layout is for the feasibility spike only. After the gate, data moves to PostgreSQL and object storage, designed in its own spec (ADR 0001, ADR 0006 "revisit after the gate"). The rules carry over; the folder names don't.

```
data/
  README.md                        TRACKED: explains this layout
  manifests/                       TRACKED: IDs, hashes, settings; never comment text
    freezes/<freeze-id>.jsonl      one row per document: IDs, SHA-256, selection reason, exclusions (ADR 0007)
    splits/<split-id>.json         dev/holdout comment IDs and hashes; the holdout lock (AM-06)
    runs/<run-id>.json             model, prompt version, input and output hashes (SiLab §4.7)
  raw/<freeze-id>/                 IGNORED: as fetched, never edited (ADR 0007)
    api/                           raw Regulations.gov JSON
    files/                         downloaded attachments
  extracted/<freeze-id>/           IGNORED: normalized per-page text JSONL
  annotations/                     IGNORED: contains quoted comment spans
    dev/
    holdout/                       kept apart so later stages can refuse to read it by default (AM-06)
  runs/<run-id>/                   IGNORED: stage outputs as JSONL
```

- **Freeze ID:** `<docket-id>.v<n>`, for example `EPA-HQ-OAR-2021-0317.v1`. A correction becomes `.v2` next to `.v1` and never overwrites it.
- **`.gitignore`:** `data/*`, then `!data/README.md` and `!data/manifests/`. Anything new under `data/` is ignored unless it's explicitly allowed.
- This spec creates only `data/README.md` and `data/manifests/{freezes,splits,runs}/.gitkeep`. The ignored folders are created by the stages that write to them (specs 003 and later).

## Package layout
```
pipeline/
  pyproject.toml          project metadata, dependencies, ruff and pytest config, entry point
  uv.lock                 committed
  .python-version         3.12
  .env.example            every variable, placeholder values only
  src/evidence_mapper/
    __init__.py           __version__ from installed package metadata
    cli.py                Typer app: --help, --version, `config check`
    config.py             Settings (Pydantic Settings)
    log.py                logging setup (named log.py so it doesn't shadow stdlib `logging`)
    acquisition.py        empty; docstring names the stage and its future spec
    extraction.py         empty
    canonicalization.py   empty
    retrieval.py          empty
    classification.py     empty
    evaluation.py         empty
  tests/
    test_cli.py
    test_config.py
    test_gitignore.py
```

- **Build backend:** `hatchling`. **Runtime dependencies:** `typer`, `pydantic`, `pydantic-settings`. **Dev dependencies** (uv dependency group): `pytest`, `ruff`.
- **Version:** declared once in `pyproject.toml` (`0.1.0`) and read at runtime with `importlib.metadata.version("evidence-mapper")`.
- **Python:** `requires-python = ">=3.12"` with `.python-version` set to `3.12`, so `uv` downloads 3.12 if the machine doesn't have it. This machine has 3.14 and no 3.12.

## Settings
| Variable | Field | Type | Required by | Secret | Default |
|---|---|---|---|---|---|
| `REGULATIONS_GOV_API_KEY` | `regulations_gov_api_key` | `SecretStr \| None` | acquisition (spec 004); `config check` | yes | none |
| `AWS_PROFILE` | `aws_profile` | `str \| None` | model calls (later spec) | no | none |
| `EVIDENCE_MAPPER_DATA_DIR` | `data_dir` | `Path` | all stages | no | `<repo>/data` |
| `EVIDENCE_MAPPER_LOG_LEVEL` | `log_level` | `str` | logging | no | `INFO` |

- **Environment only.** Settings don't read a `.env` file. To use a local `.env`, run `uv run --env-file .env evidence-mapper ...`. The app stays purely environment-driven (SP-04), and the same code runs where AWS Secrets Manager injects variables.
- **Missing settings don't fail at load** (FR-4). `--help` works on a fresh clone with nothing set. The required check lives in `Settings.require(*names)`, which raises an error naming the missing variable(s), never their values. Later stages call it.
- **The default data directory** is resolved from the package's file location (`pipeline/src/evidence_mapper/` → three levels up → `data/`), so it doesn't depend on the working directory. This works because `uv` installs the project in editable mode. A non-editable install must set `EVIDENCE_MAPPER_DATA_DIR`, and the README says so.
- `AWS_PROFILE` keeps its standard name without our prefix, because boto3 reads it directly.

## CLI
- `evidence-mapper --help`: lists commands. Exit status 0.
- `evidence-mapper --version`: prints `evidence-mapper 0.1.0`. Exit status 0.
- `evidence-mapper config check`: prints one line per setting, such as `REGULATIONS_GOV_API_KEY  set` or `EVIDENCE_MAPPER_DATA_DIR  /…/data`. Values are shown only for settings that aren't secret. Exits 1 with `Missing required setting(s): REGULATIONS_GOV_API_KEY` if any setting the pipeline requires is unset. Today that means only the API key.

## Logging (SP-01)
- Standard-library `logging` to stderr, one plain line per record (time, level, logger, message). It's configured once in `log.py` and called from the CLI callback.
- A redaction filter replaces any secret setting's value with `***` if it ever ends up in a log message. This is a backstop; the main control is that code logs only IDs, hashes, counts, timings and errors.
- The module docstring states the SP-01 rule, so later stages see it where they import the logger.

## Security and privacy
- No secrets in the repo. `.env` is already gitignored; `.env.example` holds placeholders only.
- `SecretStr` masks the key in `repr`, tracebacks and `config check` output.
- Comment data can't be committed by accident: `data/` is ignored except for manifests and its README.
- No network calls, model calls or AWS resources in this spec.

## Testing strategy
| Acceptance criterion | Test(s) | Type |
|---|---|---|
| AC-1 | `test_cli.py::test_ac1_help_exits_zero` (Typer CliRunner); `test_ac1_entry_point_help` (runs the installed `evidence-mapper` script); plus a manual fresh-clone check in T7 | unit / manual |
| AC-2 | `test_cli.py::test_ac2_version_prints_package_version` | unit |
| AC-3 | Running `uv run pytest`, `uv run ruff check .` and `uv run ruff format --check .` (T7) | manual |
| AC-4 | `test_config.py::test_ac4_config_check_names_missing_key`; `test_ac4_secret_not_in_output_or_logs` (key set to a sentinel value; checks stdout, stderr and captured logs) | unit |
| AC-5 | `test_config.py::test_ac5_env_example_lists_every_setting` (compares the variable names in `.env.example` with the Settings fields' environment names, in both directions) | unit |
| AC-6 | `test_gitignore.py::test_ac6_raw_and_extracted_ignored_manifests_tracked` (runs `git check-ignore` on sample paths under `raw/`, `extracted/`, `annotations/`, `runs/` and `manifests/`) | unit |

## Alternatives considered
- **argparse** (standard library): no dependency, but more code for subcommands and no type-hint-driven options.
- **Click:** mature, but options repeat what the type hints already say. Typer gives us Click underneath anyway.
- **Reading `.env` in Settings:** convenient, but it makes the app depend on a local file. `uv run --env-file` gives the same convenience from outside the app.
- **Listing ignored data folders one by one:** easy to forget a new folder. Default-deny is safer.
- **`uv_build` as build backend:** newer and lighter, but `hatchling` is more widely known and documented.

## Risks
- **`uv` is not installed on this machine.** T1 needs it; installing it needs your OK.
- **The editable-install path assumption** for the default data directory. Mitigated by the environment override and a README note.
- **No type checker** (mypy/pyright) is in scope. The tasks template's "type checks pass" item doesn't apply yet. Adding one is a candidate for a later spec.
