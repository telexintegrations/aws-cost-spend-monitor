# AWS Spend Monitor Integration Documentation

## Overview
AWS Spend Monitor is a FastAPI-based Telex integration that tracks AWS costs in real-time and sends alerts to Telex to help members of an organization stay within budget. It supports daily and monthly cost monitoring.

**Link:** https://aws-spend-monitor.onrender.com/integration

## What Is Telex?
Telex is an all-in-one monitoring solution for DevOps and software teams, enabling real-time communication and event logging via HTTP webhooks. It supports bulk data ingestion and integrates with platforms like Slack, Discord, and Microsoft Teams for seamless message routing.

**Link:** https://telex.im

## Integration Type
AWS Spend Monitor uses interval-based integration, meaning it is triggered at specified intervals. The user defines this interval in the integration settings using a crontab expression.

## Endpoints

### 1. **GET /integration**
Retrieves integration details, including settings, app metadata, and tick URL.
This helps in adding integration to Telex.

#### Response Example:
```json
{
  "data": {
    "date": {"created_at": "2025-02-19", "updated_at": "2025-02-19"},
    "descriptions": {
      "app_name": "AWS Spend Monitor",
      "app_description": "This app tracks AWS costs based on intervals, sending alerts to Telex to help you stay on budget.",
      "app_logo": "https://cdn.prod.website-files.com/5f05d5858fab461d0d08eaeb/654132b253b4e36b9d799ee4_6427c1d7f47c952c5838718d_2d67f7b91666ed485b01206d538bb37b_1-fc-23372-267-c-4369-8-a-31-294-c-5-f-5-fe-949.webp",
      "app_url": "https://your-api-url.com",
      "background_color": "#fff"
    },
    "is_active": false,
    "integration_type": "interval",
    "key_features": [
      "Tracks AWS spending in real-time and sends alerts.",
      "Supports daily and monthly cost monitoring.",
      "Automatically fetches AWS cost data using Cost Explorer API.",
      "Notifies users when spending exceeds the configured threshold.",
      "Allows custom threshold and frequency settings.",
      "Validates AWS credentials to prevent misconfigurations."
    ],
    "integration_category": "Finance & Payments",
    "author": "Anthony Triumph",
    "website": "https://your-api-url.com",
    "settings": [
      {"label": "aws_access_key_id", "type": "text", "required": true, "default": "key"},
      {"label": "aws_secret_access_key", "type": "text", "required": true, "default": "key"},
      {"label": "threshold", "type": "text", "required": true, "default": "100"},
      {"label": "frequency", "type": "dropdown", "options": ["Daily", "Monthly"], "description": "Select Check Frequency", "default": "Daily", "required": true},
      {"label": "interval", "type": "text", "required": true, "default": "0 0 * * *"}
    ],
    "tick_url": "https://your-api-url.com/tick",
    "target_url": ""
  }
}
```

### 2. **POST /tick**
Triggers cost monitoring based on the configured frequency and sends alerts if spending exceeds the threshold.

#### Request Body Example:
```json
{
  "return_url": "https://telex-return-webhook-url.com",
  "settings": [
    {"label": "aws_access_key_id", "type": "text", "required": true, "default": "your-key"},
    {"label": "aws_secret_access_key", "type": "text", "required": true, "default": "your-secret"},
    {"label": "threshold", "type": "text", "required": true, "default": "100"},
    {"label": "frequency", "type": "dropdown", "default": "Daily", "required": true},
    {"label": "interval", "type": "text", "required": true, "default": "0 0 * * *"}
  ]
}
```

## IAM Policy for Cost Monitoring
To allow AWS Spend Monitor to access cost data, assign the following IAM policy to your user or role:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "ce:GetCostAndUsage",
            "Resource": "*"
        }
    ]
}
```
Follow these steps to assign permissions:
1. Go to **IAM** in AWS Console.
2. Select **Users** and choose the relevant user.
3. Click **Permissions**, then **Attach policies directly**.
4. Search for the name of the policy you saved earlier and attach policy.
5. Click **Next: Review**, then **Create User**.

This grants the necessary permissions for retrieving AWS cost data.

---

## How Cost Tracking Works
1. **Determining Frequency**: The system reads the configured frequency (daily or monthly).
2. **Setting the Date Range**:
   - **Daily**: Yesterday’s cost is retrieved.
   - **Monthly**: Last month’s total cost is retrieved on the first day of the month.
3. **Querying AWS Cost Explorer**: The system fetches the AmortizedCost metric.
4. **Threshold Comparison**: If the cost exceeds the threshold, an alert is sent to Telex.

---

## Requirements
- AWS Account with Cost Explorer enabled (see configuration steps above).
- Telex account and organization.
- API access to fetch AWS cost data.

## Installation
1. **Clone the repository**
```bash
git clone https://github.com/telexintegrations/aws-cost-spend-monitor.git
cd aws-cost-spend-monitor
```
2. **Install the dependencies**
```bash
pip install -r requirements.txt
```
3. **Run the file**
```bash
python main.py
```

## Deployment
1. **Deploy API**: Host the integration on a cloud provider (e.g., AWS Lambda, Render, or Heroku). Ensure necessary environment variables (AWS keys, thresholds) are set.
2. **Install in Telex**: Provide the integration endpoint in Telex.
3. **Enable in Telex**: Enable the integration for your organization and configure settings.

## Testing

- Run Local Tests
```bash
pytest test_main.py
```
- Verify Telex messages are received with the correct AWS cost updates.

## License
This project is licensed under the [MIT License](https://github.com/telexintegrations/aws-cost-spend-monitor/blob/main/LICENSE) - see the LICENSE file for details.
