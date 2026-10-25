import pytest
from aiogram import Bot
from aiogram.utils.exceptions import NetworkError

import bot.heartbeat as heartbeat

URL = 'https://hc-ping.com/test-uuid'


class Pings(list):
    """URLs the bot pinged."""
    fail_next = False


@pytest.fixture
def pings(monkeypatch):
    sent = Pings()

    async def fake_ping(bot, url):
        if sent.fail_next:
            sent.fail_next = False
            raise RuntimeError('monitoring service is down')
        sent.append(url)

    monkeypatch.setattr(heartbeat, 'ping', fake_ping)
    monkeypatch.setattr(heartbeat, 'HEARTBEAT_URL', URL)
    monkeypatch.setattr(heartbeat, 'HEARTBEAT_INTERVAL', 0.01)

    yield sent

    heartbeat.stop_heartbeat()


def start(harness) -> None:
    # The bot starts it from prepare_all, inside the running loop
    async def run():
        heartbeat.start_heartbeat(harness.bot)

    harness.loop.run_until_complete(run())


def test_no_heartbeat_without_url(harness):
    assert heartbeat.task is None


def test_heartbeat_pings_url_repeatedly(harness, pings):
    start(harness)

    calls = harness.wait(0.05)

    assert len(pings) >= 2
    assert set(pings) == {URL}
    # Telegram is checked before each ping
    assert 'getMe' in [c.method for c in calls]


def test_no_ping_when_telegram_is_unreachable(harness, pings, monkeypatch):
    async def unreachable(self):
        raise NetworkError('Telegram is down')

    monkeypatch.setattr(Bot, 'get_me', unreachable)

    harness.loop.run_until_complete(heartbeat.beat(harness.bot))

    assert pings == []


def test_failed_ping_does_not_stop_heartbeat(harness, pings):
    pings.fail_next = True

    start(harness)
    harness.wait(0.05)

    assert not pings.fail_next
    assert URL in pings
    assert not heartbeat.task.done()


def test_shutdown_stops_heartbeat(harness, pings):
    start(harness)
    harness.wait(0.03)

    heartbeat.stop_heartbeat()
    count = len(pings)
    harness.wait(0.03)

    assert heartbeat.task is None
    assert len(pings) == count


def test_heartbeat_starts_with_the_bot(harness, pings):
    harness.restart()
    harness.wait(0.03)

    assert pings
