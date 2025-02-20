from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import boto3
from datetime import datetime, timedelta, timezone

app = FastAPI()

# Configures CORS to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Settings BaseModel class
class Setting(BaseModel):
    label: str
    type: str
    required: bool
    default: str

# Payload BaseModel class to handle return_url and settings parameters in the request payload
class Payload(BaseModel):
    return_url: str
    settings: List[Setting]

# Returns integration metadata as JSON
@app.get("/integration")
async def integration(request: Request):
    # Get base url
    base_url = str(request.base_url).rstrip("/")

    integration_json = {
        "data": {
            "date": {"created_at": "2025-02-17", "updated_at": "2025-02-17"},
            "descriptions": {
                "app_name": "AWS Spend Monitor",
                "app_description": "This app tracks AWS costs in real time, sending alerts to Telex to help you stay on budget.",
                "app_logo": "https://cdn.prod.website-files.com/5f05d5858fab461d0d08eaeb/654132b253b4e36b9d799ee4_6427c1d7f47c952c5838718d_2d67f7b91666ed485b01206d538bb37b_1-fc-23372-267-c-4369-8-a-31-294-c-5-f-5-fe-949.webp",
                "app_url": base_url,
                "background_color": "#fff",
            },
            "is_active": False,
            "integration_type": "interval",
            "key_features": [
                "Real-Time Cost Tracking",
                "Automated Alerts",
                "Simple Integration",
                "Access Cost Explorer API on you AWS account",
            ],
            "integration_category": "Finance & Payments",
            "author": "Anthony Triumph",
            "website": base_url,
            "settings": [
                {
                    "label": "aws_access_key_id", 
                    "type": "text", 
                    "required": True, 
                    "default": "key"
                },
                {
                    "label": "aws_secret_access_key", 
                    "type": "text", 
                    "required": True, 
                    "default": "key"
                },
                {
                    "label": "threshold", 
                    "type": "text", 
                    "required": True, 
                    "default": "100"
                },
                {
                    "label": "frequency",
                    "type": "dropdown",
                    "options": ["Daily", "Monthly"],
                    "description": "Select Time Period",
                    "default": "Daily",
                    "required": True
                },
                {
                    "label": "interval", 
                    "type": "text", 
                    "required": True, 
                    "default": "0 0 * * *"
                },
            ],
            "tick_url": f"{base_url}/tick",
            "target_url": ""
        }
    }
    return integration_json

# Determines cost tracking frequency based on cron-like interval
def get_frequency(interval):
    # Checks if the interval is daily
    if interval == "0 0 * * *":
        return "daily"
    # Checks if the interval is monthly
    elif interval == "0 0 1 * *":
        return "monthly"
    else:
        return "unknown"

# get_date_range function for get AWS Cost based on frequency
def get_date_range(frequency: str):
    today = datetime.now(timezone.utc).date()

    if frequency == "daily":
        start_date = today - timedelta(days=1)  # Yesterday
        end_date = today  # Today (AWS requires end_date > start_date)
    elif frequency == "monthly":
        first_day_last_month = today.replace(day=1) - timedelta(days=1)
        start_date = first_day_last_month.replace(day=1)  # Start of last month
        end_date = today  # Today

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

# query_aws_cost_api function queries the AWS cost API based on TimePeriod
def query_aws_cost_api(aws_access_key_id: str, aws_secret_access_key: str, start_date: str, end_date: str):
    try:
    # Uses AWS Cost Explorer API to retrieve amortized costs
        client = boto3.client(
            "ce", 
            region_name="us-east-1",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

    # Query STS to get account ID
        sts_client = boto3.client(
            "sts",
            region_name="us-east-1",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

        # Get the AWS account ID
        account = sts_client.get_caller_identity()["Account"]

        # Query Cost Explorer to get daily or monthly cost
        response = client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="DAILY",
            Metrics=["AmortizedCost"]
        )

        # Calculate total cost
        total_cost = sum(
            float(day["Total"]["AmortizedCost"]["Amount"]) for day in response["ResultsByTime"]
        )

        # Return total cost and account ID
        return total_cost, account

    except Exception as e:
        print(f"Error querying AWS cost API: {e}")
        return None, None

# Telex's Calls this endpoint when interval defined is reached
@app.post("/tick")
async def monitor_spending(payload: Payload):
    # Extract settings from payload
    settings = {s.label: s.default for s in payload.settings}
    aws_access_key_id = settings.get("aws_access_key_id")
    aws_secret_access_key = settings.get("aws_secret_access_key")
    threshold = int(settings.get("threshold", 0))
    frequency = settings.get("frequency", "").lower()

    # If interval is not provided, use frequency settings
    if not frequency:
        interval = settings.get("interval")
        frequency = get_frequency(interval)

    # Query AWS Cost API for current cost and account ID
    start_date, end_date = get_date_range(frequency)
    cost, account = query_aws_cost_api(aws_access_key_id, aws_secret_access_key, start_date, end_date)

    # Send Telex notification based on cost and threshold, handles exceptions also
    if account is None:
        message = "🚨 AWS Spend Monitor: Invalid AWS credentials provided. Please check your configuration."
        status = "error"
    elif cost < threshold:
        message = (
            f"✅ AWS Spend Alert\n\n"
            f"🏦 AWS Account: {account}\n"
            f"💰 Current Spend: ${cost}\n"
            f"🎯 Threshold: ${threshold}\n"
            f"🟢 Status: Within Budget"
        )
        status = "success"
    else:
        message = (
            f"🔔 AWS Spend Alert\n\n"
            f"🏦 AWS Account: {account}\n"
            f"💰 Current Spend: ${cost}\n"
            f"🎯 Threshold: ${threshold}\n"
            f"🔴 Status: Exceeded Budget"
        )
        status = "error"

    # Send Telex response using Telex way of receiving Response
    telex_format = {
        "message": message,
        "username": "AWS Spend Monitor",
        "event_name": "Cost Alert",
        "status": status
    }
    
    # Send Telex response using requests
    headers = {"Content-Type": "application/json"}
    requests.post(payload.return_url, json=telex_format, headers=headers)

    # Return success status
    return {"status": "success"}

# Running FASTAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
