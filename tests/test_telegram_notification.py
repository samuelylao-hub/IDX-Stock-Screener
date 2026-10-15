from unittest.mock import patch

from backend.app.notifications.telegram import TelegramNotificationProvider


def make_provider():
    return TelegramNotificationProvider(
        bot_token="test-token",
        chat_id="test-chat",
    )


def test_empty_message_sends_nothing():
    provider = make_provider()

    with patch.object(provider, "_send") as send:
        provider.send("")

    send.assert_not_called()


def test_long_message_is_split_within_limit():
    provider = make_provider()
    message = "x" * 9000

    with patch.object(provider, "_send") as send:
        provider.send(message)

    chunks = [call.args[0] for call in send.call_args_list]

    assert len(chunks) == 3
    assert all(0 < len(chunk) <= provider.MAX_MESSAGE_LENGTH for chunk in chunks)
    assert "".join(chunks) == message


def test_long_line_is_split_without_losing_content():
    provider = make_provider()
    message = "A" * 8500 + "\n" + "B" * 100

    with patch.object(provider, "_send") as send:
        provider.send(message)

    chunks = [call.args[0] for call in send.call_args_list]

    assert all(len(chunk) <= provider.MAX_MESSAGE_LENGTH for chunk in chunks)
    assert "".join(chunks) == message


def test_message_under_limit_is_sent_once():
    provider = make_provider()
    message = "IDX MARKET SCAN\nBBCA\nQuality: GOOD"

    with patch.object(provider, "_send") as send:
        provider.send(message)

    send.assert_called_once_with(message)



def test_long_message_is_split_under_telegram_limit():
    from unittest.mock import patch
    from backend.app.notifications.telegram import TelegramNotificationProvider

    provider = TelegramNotificationProvider("fake-token", "fake-chat")
    message = ("x" * 3999 + "\n") * 3

    with patch.object(provider, "_send") as send:
        provider.send(message)

    assert send.call_count > 1
    assert all(
        len(call.args[0]) <= provider.MAX_MESSAGE_LENGTH
        for call in send.call_args_list
    )
    assert "".join(call.args[0] for call in send.call_args_list) == message
