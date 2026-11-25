# Plan 002: Continuous integration for the pipeline

- **Spec:** [spec.md](spec.md)
- **Status:** Approved

## Approach
Add one GitHub Actions workflow, `.github/workflows/pipeline.yml`, with a single job that sets up `uv`, installs the locked dependencies and runs the three checks. GitHub Actions is GitHub's built-in automation service: a YAML file in `.github/workflows/` tells GitHub what to run on its own machines (runners) when events such as a pull request happen. No AWS, no secrets.

## Components affected
- [x] CI (`.github/workflows/pipeline.yml`)
- [x] Docs (`CLAUDE.md`, `README.md`)
- [ ] Pipeline code: none
- [ ] Infrastructure (AWS): none

## Workflow design
```yaml
name: pipeline
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: pipeline-${{ github.ref }}
  cancel-in-progress: true
jobs:
  checks:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    defaults:
      run:
        working-directory: pipeline
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1   # v7.0.1
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3
        with:
          version: "0.13.10"
          enable-cache: true
          cache-dependency-glob: pipeline/uv.lock
      - run: uv sync --locked
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pytest
```

- **No path filters.** The workflow runs on every pull request, including docs-only ones. It takes about a minute, and if branch protection later requires this check, a path-filtered workflow that never ran would block docs-only PRs.
- **`uv sync --locked`** fails if `uv.lock` doesn't match `pyproject.toml` (AC-2).
- **Python 3.12** comes from `pipeline/.python-version`; `uv` downloads it. **`uv` 0.13.10** matches the version installed locally.
- **Pinned actions (AC-5):** `actions/checkout` v7.0.1 (released 2026-07-20) and `astral-sh/setup-uv` v10.3.3 (released 2026-10-28). The latest setup-uv, v10.4.0, is only five days old, so I chose the newest release that's at least two weeks old.
- **`persist-credentials: false`** stops checkout from leaving the job's token in the local git config, where later steps could read it.
- **`concurrency`** cancels an older run when a newer commit is pushed to the same branch.
- **The checkout keeps `.gitignore`,** so the AC-6 `git check-ignore` test from spec 001 works in CI.

## Security and privacy
- `permissions: contents: read`: the workflow can read the code but can't push, comment or change settings.
- No `secrets.*` references, so pull requests from forks get nothing sensitive.
- `pull_request` (not `pull_request_target`), so fork PRs run with no write access.

## Testing strategy
CI configuration isn't covered by CLAUDE.md's testing rules. These checks verify it:

| Acceptance criterion | Check | Type |
|---|---|---|
| AC-1 | The PR for this spec shows a `pipeline / checks` result | manual (observed on GitHub) |
| AC-2 | Open a draft PR from a temporary branch and push four commits in turn, each breaking one thing (a failing test, a lint error, an unformatted file, a `pyproject.toml` change without re-locking); confirm each run fails at the expected step. Each commit reverts the previous break so only one thing fails at a time. Then close the PR unmerged and delete the branch. | manual |
| AC-3 | The PR for this spec passes | manual |
| AC-4 | `grep` the workflow for `permissions:` / `contents: read` and for `secrets.` | manual |
| AC-5 | `grep` every `uses:` line for a 40-character SHA | manual |

## Alternatives considered
- **Path filters** (run only when `pipeline/` changes): fewer runs, but they conflict with required checks later. Runs are free and fast.
- **`actions/setup-python` plus pip:** more steps, and it ignores `uv.lock`.
- **Pinning actions by version tag:** simpler, but a tag can be moved to different code. A SHA can't.

## Risks
- **The AC-2 check is visible on GitHub.** Pushes to branches other than `main` don't trigger this workflow, so the check needs a **draft pull request** from a temporary branch. It is closed unmerged and the branch deleted afterwards, but the closed PR stays in the repository's history.
- **Pinned SHAs go stale.** Updating them is manual for now; Dependabot could do it later.
