"""
Tests for project directory structure validation.
Ensures all required directories and files exist.
"""
import os
from pathlib import Path


def test_core_directories_exist():
    """Test that all core directories exist."""
    project_root = Path(__file__).parent.parent.parent

    required_dirs = [
        "core",
        "core/agents",
        "adapters",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "traces",
    ]

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Required directory missing: {dir_path}"
        assert full_path.is_dir(), f"Path exists but is not a directory: {dir_path}"


def test_python_package_init_files_exist():
    """Test that __init__.py files exist for Python packages."""
    project_root = Path(__file__).parent.parent.parent

    required_init_files = [
        "core/__init__.py",
        "core/agents/__init__.py",
        "adapters/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]

    for init_file in required_init_files:
        full_path = project_root / init_file
        assert full_path.exists(), f"Required __init__.py missing: {init_file}"
        assert full_path.is_file(), f"Path exists but is not a file: {init_file}"


def test_data_directory_is_writable():
    """Test that data directory is writable for SQLite database."""
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"

    assert os.access(data_dir, os.W_OK), "Data directory is not writable"


def test_traces_directory_is_writable():
    """Test that traces directory is writable for observability data."""
    project_root = Path(__file__).parent.parent.parent
    traces_dir = project_root / "traces"

    assert os.access(traces_dir, os.W_OK), "Traces directory is not writable"


def test_project_root_contains_claude_md():
    """Test that CLAUDE.md documentation exists."""
    project_root = Path(__file__).parent.parent.parent
    claude_md = project_root / "CLAUDE.md"

    assert claude_md.exists(), "CLAUDE.md file missing"
    assert claude_md.is_file(), "CLAUDE.md is not a file"
