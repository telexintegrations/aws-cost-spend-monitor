import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app, get_frequency, get_date_range, query_aws_cost_api
from datetime import timedelta, datetime

client = TestClient(app)

# Test get_frequency function
@pytest.mark.parametrize("interval, expected", [
    ("0 0 * * *", "daily"),
    ("0 0 * * 1", "unknown"),
    ("0 0 1 * *", "monthly"),
])
def test_get_frequency(interval, expected):
    assert get_frequency(interval) == expected

# Test get_date_range function
@pytest.mark.parametrize("frequency", [
    "daily",
    "monthly",
])
def test_get_date_range(frequency):
    # Dynamically calculate expected dates
    today = datetime.today().date()

    if frequency == "daily":
        expected_start = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        expected_end = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif frequency == "monthly":
        first_day_last_month = today.replace(day=1) - timedelta(days=1)
        expected_start = first_day_last_month.replace(day=1).strftime("%Y-%m-%d")
        expected_end = first_day_last_month.strftime("%Y-%m-%d")

    start_date, end_date = get_date_range(frequency)

    assert start_date == expected_start
    assert end_date == expected_end


# Mock AWS Cost Explorer API response
@patch("main.boto3.client")
def test_query_aws_cost_api(mock_boto_client):
    mock_client = mock_boto_client.return_value
    mock_client.get_cost_and_usage.return_value = {
        "ResultsByTime": [{"Total": {"AmortizedCost": {"Amount": "50.00"}}}]
    }
    mock_client.get_caller_identity.return_value = {"Account": "123456789"}

    cost, account = query_aws_cost_api("fake_key", "fake_secret", "2025-02-01", "2025-02-17")

    assert cost == 50.00
    assert account == "123456789"

# Test integration endpoint
def test_integration():
    response = client.get("/integration")
    assert response.status_code == 200
    json_data = response.json()
    assert "data" in json_data
    assert json_data["data"]["descriptions"]["app_name"] == "AWS Spend Monitor"

# Mock AWS in /tick endpoint
@patch("main.query_aws_cost_api")
def test_monitor_spending(mock_query_aws):
    mock_query_aws.return_value = (50.00, "123456789")

    test_payload = {
        "return_url": "http://example.com",
        "settings": [
            {"label": "aws_access_key_id", "type": "text", "required": True, "default": "test_key"},
            {"label": "aws_secret_access_key", "type": "text", "required": True, "default": "test_secret"},
            {"label": "threshold", "type": "text", "required": True, "default": "100"},
            {"label": "frequency", "type": "dropdown", "required": True, "default": "Daily"},
            {"label": "interval", "type": "text", "required": True, "default": "0 0 * * *"},
        ]
    }

    response = client.post("/tick", json=test_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
