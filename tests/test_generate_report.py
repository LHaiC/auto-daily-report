import json
import pathlib
from unittest import mock

import scripts.generate_report as gr


def test_extract_by_path():
    obj = {"choices": [{"message": {"content": "ok"}}]}
    assert gr.extract_by_path(obj, "choices.0.message.content") == "ok"


def test_replace_placeholders():
    t = {"a": "{{x}}", "b": [{"c": "{{y}}"}]}
    out = gr.replace_placeholders(t, {"x": "1", "y": "2"})
    assert out == {"a": "1", "b": [{"c": "2"}]}


def test_ensure_minimum_sections_fallback():
    out = gr.ensure_minimum_sections("hello", "2026-02-17")
    assert "## What I Did Today" in out
    assert "Raw Model Output" in out


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@mock.patch("urllib.request.urlopen")
def test_call_cloud_api_default_openai(mock_urlopen, monkeypatch):
    payload = {"choices": [{"message": {"content": "# Daily Report - 2026-02-17\n\n## What I Did Today\n- x\n## Problems / Blockers\n- x\n## Root Cause\n- x\n## Attempts & Fixes\n- x\n## Key Learnings\n- x\n## Metrics\n- x\n## Next Steps (Tomorrow)\n- [ ] x"}}]}
    mock_urlopen.return_value = _FakeResp(payload)

    monkeypatch.setenv("REPORT_API_URL", "https://api.example.com/v1/chat/completions")
    monkeypatch.setenv("REPORT_API_KEY", "k")
    monkeypatch.setenv("REPORT_API_MODEL", "demo")
    monkeypatch.delenv("REPORT_API_REQUEST_TEMPLATE_JSON", raising=False)
    monkeypatch.setenv("REPORT_API_RESPONSE_PATH", "choices.0.message.content")

    out = gr.call_cloud_api("u", "s")
    assert "Daily Report" in out


@mock.patch("urllib.request.urlopen")
def test_call_cloud_api_custom_template(mock_urlopen, monkeypatch):
    payload = {"data": {"text": "custom-ok"}}
    mock_urlopen.return_value = _FakeResp(payload)

    monkeypatch.setenv("REPORT_API_URL", "https://api.example.com/generate")
    monkeypatch.setenv("REPORT_API_KEY", "k")
    monkeypatch.setenv("REPORT_API_AUTH_SCHEME", "")
    monkeypatch.setenv("REPORT_API_RESPONSE_PATH", "data.text")
    monkeypatch.setenv(
        "REPORT_API_REQUEST_TEMPLATE_JSON",
        json.dumps({"model": "{{model}}", "input": "{{user_prompt}}", "system": "{{system_prompt}}"}),
    )
    monkeypatch.setenv("REPORT_API_MODEL", "m1")

    out = gr.call_cloud_api("hello", "world")
    assert out == "custom-ok"


def test_build_user_prompt():
    p = gr.build_user_prompt("raw", "issue", "12", "2026-02-17")
    assert "issue:12" in p
    assert "raw" in p
