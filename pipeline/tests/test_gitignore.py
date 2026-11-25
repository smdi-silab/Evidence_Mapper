"""AC-6: raw and extracted data are gitignored; manifests are tracked."""

import shutil
import subprocess

import pytest

from evidence_mapper.config import REPO_ROOT

IGNORED = [
    "data/raw/EPA-HQ-OAR-2021-0317.v1/api/comment.json",
    "data/raw/EPA-HQ-OAR-2021-0317.v1/files/attachment.pdf",
    "data/extracted/EPA-HQ-OAR-2021-0317.v1/pages.jsonl",
    "data/annotations/holdout/labels.jsonl",
    "data/runs/run-001/claims.jsonl",
    "data/anything-new/file.txt",
]
TRACKED = [
    "data/README.md",
    "data/manifests/freezes/EPA-HQ-OAR-2021-0317.v1.jsonl",
    "data/manifests/splits/split-v1.json",
    "data/manifests/runs/run-001.json",
]


def _is_ignored(path: str) -> bool:
    git = shutil.which("git")
    assert git is not None
    result = subprocess.run(
        [git, "check-ignore", "--no-index", "-q", path], cwd=REPO_ROOT, check=False
    )
    assert result.returncode in (0, 1), f"git check-ignore failed for {path}"
    return result.returncode == 0


@pytest.mark.parametrize("path", IGNORED)
def test_ac6_data_paths_ignored(path: str) -> None:
    assert _is_ignored(path)


@pytest.mark.parametrize("path", TRACKED)
def test_ac6_manifest_paths_not_ignored(path: str) -> None:
    assert not _is_ignored(path)
