"""CLI defaults stay read-only; never run a provider or real database here."""
import sys

import pytest

from api.config import billing as config
from api.services import billing_events
from scripts.replay_billing_event import main


@pytest.fixture
def cli(monkeypatch):
    monkeypatch.setattr(config, 'STRIPE_SECRET_KEY', 'sk_test_fixture')
    calls = []
    monkeypatch.setattr(billing_events, 'inspect_replay', lambda *a: {'replayable': True})
    monkeypatch.setattr(billing_events, 'process_receipt', lambda *a, **kw: calls.append(kw))
    def run(*args):
        monkeypatch.setattr(sys, 'argv', ['replay_billing_event', '--mode', 'test',
                                         '--event-id', 'evt_fixture', *args])
        main()
    return run, calls


def test_default_is_dry_run(cli):
    run, calls = cli
    run()
    assert calls == []


def test_apply_requires_operator_reason(cli):
    run, calls = cli
    with pytest.raises(SystemExit):
        run('--apply')
    assert calls == []


def test_apply_refuses_superseded_receipt(cli, monkeypatch):
    run, calls = cli
    monkeypatch.setattr(billing_events, 'inspect_replay', lambda *a: {'replayable': False})
    with pytest.raises(SystemExit):
        run('--apply', '--reason', 'reviewed')
    assert calls == []


def test_apply_refuses_wrong_server_mode(cli, monkeypatch):
    run, calls = cli
    monkeypatch.setattr(config, 'STRIPE_SECRET_KEY', 'sk_live_fixture')
    with pytest.raises(SystemExit):
        run('--apply', '--reason', 'reviewed')
    assert calls == []


def test_explicit_apply_passes_review_reason(cli):
    run, calls = cli
    run('--apply', '--reason', 'mapping corrected')
    assert calls == [{'replay_reason': 'mapping corrected'}]
