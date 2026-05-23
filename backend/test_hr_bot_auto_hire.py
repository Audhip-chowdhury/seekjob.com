"""Unit tests for hr-bot auto-hire trigger (run: python -m pytest test_hr_bot_auto_hire.py -q)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import recruitment_webhook as wh


def test_build_hr_bot_auto_hire_payload_defaults():
    payload = wh.build_hr_bot_auto_hire_payload(42)
    assert payload["seekjob_job_id"] == 42
    assert payload["role"]["select_for_role_after_screen"] is True
    assert payload["role"]["skip_role_per_user_screening"] is True
    assert "company_email" not in payload


def test_build_hr_bot_auto_hire_payload_with_credentials(monkeypatch):
    monkeypatch.setenv("HR_BOT_AUTO_HIRE_COMPANY_EMAIL", "co@example.com")
    monkeypatch.setenv("HR_BOT_AUTO_HIRE_COMPANY_PASSWORD", "secret")
    payload = wh.build_hr_bot_auto_hire_payload(7)
    assert payload["company_email"] == "co@example.com"
    assert payload["company_password"] == "secret"


def test_trigger_skipped_when_url_unset(monkeypatch):
    monkeypatch.delenv("HR_BOT_AUTO_HIRE_URL", raising=False)
    monkeypatch.setenv("HUMAN_PRESENT", "0")
    with patch.object(wh.requests, "post") as post:
        wh.trigger_hr_bot_auto_hire_seekjob(1, application_id=99)
        post.assert_not_called()


def test_trigger_skipped_when_human_present(monkeypatch):
    monkeypatch.setenv("HUMAN_PRESENT", "1")
    monkeypatch.setenv("HR_BOT_AUTO_HIRE_URL", "http://127.0.0.1:8010/hr/screen-seekjob-posting-no-reject")
    with patch.object(wh.requests, "post") as post:
        wh.trigger_hr_bot_auto_hire_seekjob(1, application_id=99)
        post.assert_not_called()


def test_schedule_skipped_when_human_present(monkeypatch):
    monkeypatch.setenv("HUMAN_PRESENT", "1")
    with patch.object(wh, "trigger_hr_bot_auto_hire_seekjob") as trigger:
        wh.schedule_hr_bot_auto_hire_on_apply(3, application_id=1)
        import time

        time.sleep(0.1)
        trigger.assert_not_called()


def test_trigger_posts_when_url_set(monkeypatch):
    monkeypatch.setenv("HUMAN_PRESENT", "0")
    monkeypatch.setenv("HR_BOT_AUTO_HIRE_URL", "http://127.0.0.1:8010/hr/screen-seekjob-posting-no-reject")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = '{"ok":true}'
    with patch.object(wh.requests, "post", return_value=mock_resp) as post:
        wh.trigger_hr_bot_auto_hire_seekjob(5, application_id=10)
        post.assert_called_once()
        call_kw = post.call_args.kwargs
        assert call_kw["json"]["seekjob_job_id"] == 5
        assert call_kw["timeout"] == wh.DEFAULT_HR_BOT_AUTO_HIRE_TIMEOUT


def test_schedule_starts_background_thread(monkeypatch):
    monkeypatch.setenv("HUMAN_PRESENT", "0")
    monkeypatch.setenv("HR_BOT_AUTO_HIRE_URL", "http://example/hr/screen-seekjob-posting-no-reject")
    with patch.object(wh, "trigger_hr_bot_auto_hire_seekjob") as trigger:
        wh.schedule_hr_bot_auto_hire_on_apply(3, application_id=1)
        import time

        time.sleep(0.2)
        trigger.assert_called_once_with(3, application_id=1)
