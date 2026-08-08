"""
CRM webhook integration service.
Handles syncing approved responses to third-party CRM systems via HTTP webhooks.
"""

import logging
import requests
from typing import Dict, Optional
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from core.exceptions import CRMSyncError

logger = logging.getLogger('llm')


def sync_to_crm(
    response_obj,
    webhook_url: str,
    payload: Dict,
    retry_attempt: int = 0
) -> bool:
    """
    Sync approved response to CRM webhook.

    Args:
        response_obj: Response model instance
        webhook_url: CRM webhook URL
        payload: Data payload to send to CRM
        retry_attempt: Current retry attempt number

    Returns:
        True if sync successful, False otherwise
    """
    try:
        logger.info(f"Syncing response {response_obj.id} to CRM: {webhook_url}")

        # Set timeout
        timeout = settings.CRM_WEBHOOK_TIMEOUT

        # Make POST request to CRM webhook
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'ConversationAI/1.0'
            }
        )

        # Check response status
        if response.status_code in [200, 201, 202]:
            logger.info(f"Successfully synced response {response_obj.id} to CRM (HTTP {response.status_code})")
            _log_crm_sync(response_obj, webhook_url, 'success', response.status_code)
            return True
        else:
            logger.warning(f"CRM webhook returned HTTP {response.status_code} for response {response_obj.id}")
            _log_crm_sync(response_obj, webhook_url, 'failed', response.status_code, response.text)

            # Retry if configured
            if _should_retry(retry_attempt):
                return _retry_with_backoff(response_obj, webhook_url, payload, retry_attempt)

            return False

    except requests.Timeout:
        logger.error(f"Timeout while syncing response {response_obj.id} to CRM")
        _log_crm_sync(response_obj, webhook_url, 'failed', error_message="Timeout")

        if _should_retry(retry_attempt):
            return _retry_with_backoff(response_obj, webhook_url, payload, retry_attempt)

        return False

    except requests.RequestException as e:
        logger.error(f"Request error while syncing response {response_obj.id}: {str(e)}")
        _log_crm_sync(response_obj, webhook_url, 'failed', error_message=str(e))

        if _should_retry(retry_attempt):
            return _retry_with_backoff(response_obj, webhook_url, payload, retry_attempt)

        return False

    except Exception as e:
        logger.error(f"Unexpected error syncing response {response_obj.id}: {str(e)}")
        _log_crm_sync(response_obj, webhook_url, 'failed', error_message=str(e))
        return False


def _should_retry(retry_attempt: int) -> bool:
    """Check if should retry based on configured max attempts."""
    max_retries = settings.CRM_WEBHOOK_RETRY_ATTEMPTS
    return retry_attempt < max_retries


def _retry_with_backoff(
    response_obj,
    webhook_url: str,
    payload: Dict,
    current_attempt: int
) -> bool:
    """
    Retry with exponential backoff.
    In production, this should be a Celery task for async retry.
    """
    # Exponential backoff: 2^attempt seconds
    wait_time = 2 ** current_attempt

    logger.info(f"Retrying sync for response {response_obj.id} in {wait_time}s (attempt {current_attempt + 1})")

    # In a production system, use Celery for async retry:
    # from celery import current_app
    # current_app.send_task('sync_response_to_crm', args=[response_obj.id], countdown=wait_time)

    # For now, just log that retry would happen
    return False


def _log_crm_sync(
    response_obj,
    webhook_url: str,
    status: str,
    response_code: Optional[int] = None,
    error_message: str = ''
):
    """Log CRM sync attempt."""
    try:
        from apps.integrations.models import CRMLog

        crm_log, created = CRMLog.objects.get_or_create(
            response=response_obj,
            defaults={
                'webhook_url': webhook_url,
                'status': status,
                'response_code': response_code,
                'attempt_count': 1,
                'last_attempt_at': timezone.now(),
                'error_message': error_message
            }
        )

        if not created:
            crm_log.status = status
            crm_log.response_code = response_code
            crm_log.attempt_count += 1
            crm_log.last_attempt_at = timezone.now()
            if error_message:
                crm_log.error_message = error_message
            crm_log.save()

        logger.debug(f"Logged CRM sync for response {response_obj.id}: {status}")

    except Exception as e:
        logger.error(f"Failed to log CRM sync: {str(e)}")


def validate_webhook_url(url: str) -> bool:
    """Validate webhook URL format."""
    if not url or not isinstance(url, str):
        return False

    return url.startswith(('http://', 'https://'))


def test_webhook_connection(webhook_url: str) -> bool:
    """Test webhook connectivity with a ping."""
    try:
        response = requests.post(
            webhook_url,
            json={'test': True},
            timeout=5
        )
        return response.status_code < 500
    except Exception:
        return False
