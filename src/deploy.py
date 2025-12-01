#!/usr/bin/env python3
"""
Dokploy Deployment Action - Main Script

Triggers and monitors Dokploy deployments with proper verification
to avoid race conditions and ensure deployments actually complete.
"""

import os
import sys
import time
from typing import Optional

from .logger import create_logger
from .dokploy_client import DokployClient, DokployAPIError
from .deployment_tracker import (
    DeploymentTracker,
    DeploymentNotFoundError,
    DeploymentFailedError,
    DeploymentTimeoutError
)


def get_env(name: str, required: bool = True) -> Optional[str]:
    """Get environment variable with optional requirement check."""
    value = os.getenv(name)
    if required and not value:
        print(f"::error::Missing required environment variable: {name}")
        sys.exit(1)
    return value


def str_to_bool(value: str) -> bool:
    """Convert string to boolean."""
    return value.lower() in ('true', '1', 'yes')


def main() -> int:
    """Main deployment orchestration."""

    # Create logger
    logger = create_logger()

    try:
        # Read configuration from environment (set by GitHub Action)
        dokploy_url = get_env('INPUT_DOKPLOY_URL')
        auth_token = get_env('INPUT_AUTH_TOKEN')
        application_id = get_env('INPUT_APPLICATION_ID')
        application_name = get_env('INPUT_APPLICATION_NAME')
        wait_for_completion = str_to_bool(get_env('INPUT_WAIT_FOR_COMPLETION', required=False) or 'false')
        restart = str_to_bool(get_env('INPUT_RESTART', required=False) or 'false')
        skip_deploy = str_to_bool(get_env('INPUT_SKIP_DEPLOY', required=False) or 'false')

        logger.info(f"Dokploy Deployment Action")
        logger.info(f"Application: {application_name} ({application_id})")
        logger.info(f"Wait for completion: {wait_for_completion}")
        logger.info(f"Restart after deploy: {restart}")

        # Initialize client and tracker
        client = DokployClient(dokploy_url, auth_token, logger)
        tracker = DeploymentTracker(client, logger)

        # Skip deployment if requested
        if skip_deploy:
            logger.info("Skipping deployment (SKIP_DEPLOY=true)")
            return 0

        # PHASE 1: Get baseline deployment (before triggering)
        # This is critical to identify which deployment we triggered
        logger.info("Getting current deployment state...")
        deployments = client.get_deployments(application_id)

        baseline_timestamp = None
        if deployments:
            latest = deployments[0]
            baseline_timestamp = latest.get('createdAt')
            logger.info(
                f"Latest deployment: {latest['deploymentId']} "
                f"(status: {latest['status']}, created: {baseline_timestamp})"
            )
        else:
            logger.info("No previous deployments found")

        # PHASE 2: Trigger new deployment
        client.deploy(application_id)

        # If not waiting for completion, exit now
        if not wait_for_completion:
            logger.info(
                "Deployment triggered. Not waiting for completion "
                "(wait_for_completion=false)"
            )
            logger.warning(
                "⚠️  Action will exit without verifying deployment succeeded. "
                "Consider setting wait_for_completion=true to ensure deployment completes."
            )
            return 0

        # PHASE 3: Track deployment to completion
        with logger.group("Tracking deployment progress"):
            try:
                final_deployment = tracker.track_deployment(
                    application_id=application_id,
                    baseline_timestamp=baseline_timestamp,
                    # timeout=600  # 10 minutes default for builds
                )

                deployment_id = final_deployment['deploymentId']
                logger.success(f"Deployment verified: {deployment_id}")

            except DeploymentNotFoundError as e:
                logger.error(str(e))
                logger.error(
                    "The deployment was triggered but never appeared in the deployment list. "
                    "This could indicate:\n"
                    "  1. The application doesn't exist or ID is wrong\n"
                    "  2. Dokploy is experiencing issues\n"
                    "  3. The deployment was queued but hasn't started"
                )
                return 1

            except DeploymentFailedError as e:
                logger.error(str(e))
                if 'errorMessage' in final_deployment:
                    logger.error(f"Error details: {final_deployment['errorMessage']}")
                if 'logPath' in final_deployment:
                    logger.info(f"Check logs at: {final_deployment['logPath']}")
                return 1

            except DeploymentTimeoutError as e:
                logger.error(str(e))
                logger.error(
                    "Deployment did not complete within the timeout period. "
                    "This could mean:\n"
                    "  1. The build is taking longer than expected (increase timeout)\n"
                    "  2. The deployment is stuck\n"
                    "  3. Dokploy is experiencing issues"
                )
                return 1

        # PHASE 4: Optional restart
        # Only restart if explicitly requested AND deployment succeeded
        if restart:
            logger.info("Restart requested, stopping and starting application...")

            with logger.group("Restarting application"):
                try:
                    # Stop application
                    client.stop(application_id)

                    # Brief pause to ensure clean stop
                    logger.info("Waiting 5 seconds for clean shutdown...")
                    time.sleep(5)

                    # Start with new version
                    client.start(application_id)

                    # Verify application is running
                    logger.info("Waiting 10 seconds for application to start...")
                    time.sleep(10)

                    app = client.get_application(application_id)
                    app_status = app.get('applicationStatus', 'unknown')

                    if app_status in ('done', 'running'):
                        logger.success(f"Application restarted successfully (status: {app_status})")
                    else:
                        logger.warning(
                            f"Application restarted but status is '{app_status}'. "
                            "Please verify manually."
                        )

                except DokployAPIError as e:
                    logger.error(f"Restart failed: {e}")
                    logger.error("Deployment succeeded but restart failed. Application may be in inconsistent state.")
                    return 1

        # Success!
        logger.success(
            f"✓ Deployment completed successfully for {application_name}"
        )
        return 0

    except DokployAPIError as e:
        logger.error(f"Dokploy API error: {e}")
        return 1

    except KeyboardInterrupt:
        logger.warning("Deployment cancelled by user")
        return 130

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())
