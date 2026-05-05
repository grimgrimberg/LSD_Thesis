import subprocess
from pathlib import Path

from lsd_thesis.utils import get_version_stamp


def test_get_version_stamp_reports_not_repo(tmp_path: Path) -> None:
    stamp = get_version_stamp(tmp_path)

    assert stamp["git"]["repo_present"] is False
    assert stamp["git"]["branch"] is None
    assert stamp["git"]["head_present"] is False
    assert stamp["git"]["commit_hash"] is None
    assert stamp["git"]["worktree_status"] == "not_repo"


def test_get_version_stamp_reports_unborn_head(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)

    stamp = get_version_stamp(repo_root)

    assert stamp["git"]["repo_present"] is True
    assert stamp["git"]["branch"] is not None
    assert stamp["git"]["head_present"] is False
    assert stamp["git"]["commit_hash"] is None
    assert stamp["git"]["worktree_status"] == "unborn"


def test_get_version_stamp_reports_valid_head(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True, capture_output=True, text=True)
    (repo_root / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)

    stamp = get_version_stamp(repo_root)

    assert stamp["git"]["repo_present"] is True
    assert stamp["git"]["head_present"] is True
    assert stamp["git"]["commit_hash"]
    assert stamp["git"]["worktree_status"] == "clean"
