import os
from unittest.mock import patch, MagicMock
from plugins.ingest_github import fetch_github_data

@patch("plugins.ingest_github.requests.get")
@patch.dict(os.environ, {"DEMO_MODE": "false", "GITHUB_API_TOKEN": "mock_token"})
def test_fetch_github_data_pagination(mock_get):
    """Test if pagination correctly follows the 'next' link."""
    # Mock first response
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = [{"id": 1}]
    mock_response_1.links = {"next": {"url": "http://api.github.com/next"}}
    
    # Mock second response
    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = [{"id": 2}]
    mock_response_2.links = {} # No more pages
    
    mock_get.side_effect = [mock_response_1, mock_response_2]
    
    data = list(fetch_github_data("pulls", repo="test/repo"))
    
    assert len(data) == 2
    assert data[0][0]["id"] == 1
    assert data[1][0]["id"] == 2
    assert mock_get.call_count == 2

@patch("plugins.ingest_github.time.sleep")
@patch("plugins.ingest_github.requests.get")
@patch.dict(os.environ, {"DEMO_MODE": "false"})
def test_fetch_github_data_backoff(mock_get, mock_sleep):
    """Test exponential backoff on 429 Rate Limit."""
    mock_rate_limit = MagicMock()
    mock_rate_limit.status_code = 429
    mock_rate_limit.headers = {"X-RateLimit-Reset": "1999999999"}
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = [{"id": 1}]
    mock_success.links = {}
    
    mock_get.side_effect = [mock_rate_limit, mock_success]
    
    data = list(fetch_github_data("pulls", repo="test/repo"))
    
    assert len(data) == 1
    assert mock_get.call_count == 2
    assert mock_sleep.call_count == 1
