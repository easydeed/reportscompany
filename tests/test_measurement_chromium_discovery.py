"""Measurement gates must find the Chromium that CI actually installed."""
import importlib.util
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


@pytest.fixture(params=[
    "measure_contrast_by_pixel",
    "measure_pdf_contrast",
    "measure_market_pagination",
    "measure_gallery_continuation_fit",
])
def measurement(request, monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location(
        request.param, SCRIPTS / f"{request.param}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "empty-home")
    return module


@pytest.mark.parametrize("layout", ["chrome-linux", "chrome-linux64"])
def test_finds_installed_browser_in_either_layout(measurement, tmp_path, layout):
    executable = tmp_path / "chromium-1234" / layout / "chrome"
    executable.parent.mkdir(parents=True)
    executable.touch()
    assert measurement.find_chromium() == str(executable)


def test_both_layouts_can_coexist(measurement, tmp_path):
    for revision, layout in [("1234", "chrome-linux"), ("1235", "chrome-linux64")]:
        executable = tmp_path / f"chromium-{revision}" / layout / "chrome"
        executable.parent.mkdir(parents=True)
        executable.touch()
    assert measurement.find_chromium() == str(executable)


def test_missing_browser_preserves_playwright_fallback(measurement):
    assert measurement.find_chromium() == ""
