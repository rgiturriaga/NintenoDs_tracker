import pytest
import requests

import utils

def test_send_telegram_alert_success(mocker):
    """Test successful Telegram notification dispatch."""
    # Mock environment variables
    mocker.patch.dict(os.environ, {
        "TELEGRAM_TOKEN": "12345678:ABC-DEF1234ghIkl-zyx987wuvUT",
        "TELEGRAM_CHAT_ID": "987654321"
    })
    
    # Mock the post request inside utils._session
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True, "result": "Message sent"}
    
    mock_post = mocker.patch.object(utils._session, "post", return_value=mock_response)
    
    res = utils.send_telegram_alert("Hello World")
    
    assert res == {"ok": True, "result": "Message sent"}
    mock_post.assert_called_once()
    # Check that payload parameters were sent correctly
    called_args, called_kwargs = mock_post.call_args
    assert called_kwargs["data"]["chat_id"] == "987654321"
    assert called_kwargs["data"]["text"] == "Hello World"
    assert called_kwargs["data"]["parse_mode"] == "HTML"

def test_send_telegram_alert_missing_credentials(mocker):
    """Test behavior when Telegram credentials are missing in the environment."""
    # Ensure variables are removed
    mocker.patch.dict(os.environ, {}, clear=True)
    
    res = utils.send_telegram_alert("Hello World")
    
    # Should exit early and return None
    assert res is None

def test_send_telegram_alert_api_failure(mocker):
    """Test behavior when the Telegram API returns a non-200 response."""
    mocker.patch.dict(os.environ, {
        "TELEGRAM_TOKEN": "12345678:ABC-DEF1234ghIkl-zyx987wuvUT",
        "TELEGRAM_CHAT_ID": "987654321"
    })
    
    mock_response = mocker.MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Client Error: Unauthorized")
    
    mocker.patch.object(utils._session, "post", return_value=mock_response)
    
    res = utils.send_telegram_alert("Hello World")
    
    # Should catch exception and return None
    assert res is None

def test_send_telegram_alert_network_exception(mocker):
    """Test behavior when the post request raises a network connection exception."""
    mocker.patch.dict(os.environ, {
        "TELEGRAM_TOKEN": "12345678:ABC-DEF1234ghIkl-zyx987wuvUT",
        "TELEGRAM_CHAT_ID": "987654321"
    })
    
    mocker.patch.object(utils._session, "post", side_effect=requests.exceptions.ConnectionError("Connection timed out"))
    
    res = utils.send_telegram_alert("Hello World")
    
    # Should gracefully catch the exception, log it, and return None
    assert res is None
