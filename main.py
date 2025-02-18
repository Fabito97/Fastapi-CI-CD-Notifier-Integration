import asyncio
import json
import httpx
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from fastapi import HTTPException


class Setting(BaseModel):
    label: str
    type: str
    required: bool
    default: str

class NotifyPayload(BaseModel):
    settings: List[Setting]
    message: str  
   

Slack_Webhook_Url = "https://hooks.slack.com/services/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"


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://staging.telextest.im", 
        "http://telextest.im", 
        "https://staging.telex.im", 
        "https://telex.im"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/integration.json")
def get_integration_json(request: Request):
    base_url = str(request.base_url).rstrip("/")

    integration_json = {
        "data": {
            "date": {
                "created_at": "2025-02-16",
                "updated_at": "2025-02-16"
            },
            "descriptions": {
                "app_name": "CI/CD Notifier",
                "app_description": "A notifier for the operation",
                "app_logo": "https://i.imgur.com/1Zqvffp.png",
                "app_url": base_url,
                "background_color": "#fff",
            },
            "is_active": True,            
            "integration_type": "output",
            "key_features": [
                "- provides notification from ci/cd operation",
                "- sends the notification to your slack channel"
            ],           
            "integration_category": "DevOps & CI/CD",
            "author": "Fabian Muoghalu",
            "website": base_url,
            "settings": [
                {
                    "label": "slack-webhook-url",
                    "type": "text",
                    "required": True,
                    "default": Slack_Webhook_Url
                }
            ],
            "target_url": f"{base_url}/notify"
        }
    }

    return integration_json


async def send_slack_notification(slack_webhook: str, message: dict):
    """Sends the notification to Slack asynchronously."""

    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(slack_webhook, json=message, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"Slack notification failed: {e}")


@app.post("/notify")
async def send_message(payload: NotifyPayload, background_tasks: BackgroundTasks):
    """Handles Telex's notification request and forwards it to slack asynchronously."""   
    
    # Extract Slack webhook URL from settings
    slack_webhook = next(
        (setting.default for setting in payload.settings if setting.label == "slack-webhook-url"), 
        None
    )

    if not slack_webhook:
        raise HTTPException(status_code=400, detail="Slack webhook URL not found in settings")
   

    message = {
        "text": f"🔔 *CI/CD Deployment Notification*\n"
                f"📂 *Message:* {payload.message}"                
    }
    
    # Process Slack notification in the background
    background_tasks.add_task(send_slack_notification, slack_webhook, message)
     
    return {"status": "Accepted"}, 202

