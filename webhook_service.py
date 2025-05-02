import logging
import httpx
from typing import Any, Dict
from task_repository import (
    update_task_run,
)

logger = logging.getLogger(__name__)

async def post_webhook(webhook_url: str, data: Any, task_run_id: int):
    """
    Post data to a webhook URL and update the task run with the result.
    
    Args:
        webhook_url: The URL to post the data to
        data: The data to post
        task_run_id: The ID of the task run
    """
    if not webhook_url:
        logger.info("No webhook URL provided, skipping webhook")
        return
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=data)
            if response.status_code < 400:
                logger.info(f"Success to send webhook: {response.status_code} - {response.text}")
                update_data = {
                    "webhook_result_success": True,
                    "webhook_result_status_code": response.status_code,
                    "webhook_result_message": response.text,
                }

                update_task_run(
                    task_run_id=task_run_id,
                    data=update_data,
                )
                
            else:
                logger.error(f"Failed to send webhook: {response.status_code} - {response.text}")
                update_data = {
                    "webhook_result_success": False,
                    "webhook_result_status_code": response.status_code,
                    "webhook_result_message": response.text,
                }

                update_task_run(
                    task_run_id=task_run_id,
                    data=update_data,
                )
    except Exception as e:
        logger.error(f"Failed to send webhook: {e}")
        update_data = {
            "webhook_result_success": False,
            "webhook_result_status_code": 500,
            "webhook_result_message": f"Error sending webhook: {str(e)}",
        }
        update_task_run(
            task_run_id=task_run_id,
            data=update_data,
        )
