from unittest.mock import MagicMock
from plugins.ingest_github import ingest_to_db

def test_ingest_to_db_idempotency():
    """Test that ingest_to_db uses ON CONFLICT DO UPDATE so it's idempotent."""
    mock_cursor = MagicMock()
    
    data = [
        {"id": 1, "number": 10, "title": "Test", "state": "open", "created_at": "2023-01-01T00:00:00Z", "updated_at": "2023-01-01T00:00:00Z"}
    ]
    
    ingest_to_db(data, "pull_requests", mock_cursor)
    
    assert mock_cursor.execute.call_count == 1
    query, params = mock_cursor.execute.call_args[0]
    
    # Assert query contains the UPSERT clause
    assert "ON CONFLICT (id) DO UPDATE" in query
    
    # Assert params match the mock data
    assert params[0] == 1 # id
    assert params[1] == 10 # number
