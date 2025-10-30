"""
Deployment tracker for monitoring and verifying Dokploy deployments.
Handles the critical logic of finding the triggered deployment and tracking it to completion.
"""

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from src.dokploy_client import DokployClient, DokployAPIError
from src.logger import DeployLogger


class DeploymentNotFoundError(Exception):
    """Raised when the triggered deployment cannot be found."""
    pass


class DeploymentFailedError(Exception):
    """Raised when deployment fails."""
    pass


class DeploymentTimeoutError(Exception):
    """Raised when deployment times out."""
    pass


class DeploymentTracker:
    """
    Tracks Dokploy deployments from trigger to completion.

    This class solves the race condition where the action would check applicationStatus
    (which might be "done" from a previous deployment) instead of tracking the specific
    deployment that was just triggered.

    Strategy:
    1. Capture timestamp of latest deployment before triggering
    2. Trigger new deployment
    3. Poll for NEW deployment created after the baseline timestamp
    4. Track that specific deployment by ID until completion
    """

    def __init__(self, client: DokployClient, logger: DeployLogger):
        self.client = client
        self.logger = logger

    def _parse_timestamp(self, timestamp: Optional[str]) -> Optional[datetime]:
        """Parse ISO timestamp string to datetime."""
        if not timestamp:
            return None
        try:
            # Remove 'Z' and parse
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    def _find_deployment_after(
        self,
        deployments: List[Dict[str, Any]],
        baseline_timestamp: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the first deployment created after the baseline timestamp.

        Args:
            deployments: List of deployments (newest first)
            baseline_timestamp: ISO timestamp to compare against

        Returns:
            The newest deployment created after baseline, or None if not found
        """
        if not deployments:
            return None

        # If no baseline, return the newest deployment
        if not baseline_timestamp:
            return deployments[0]

        baseline_dt = self._parse_timestamp(baseline_timestamp)
        if not baseline_dt:
            return deployments[0]

        # Find first deployment created after baseline
        for deployment in deployments:
            created_at = self._parse_timestamp(deployment.get('createdAt'))
            if created_at and created_at > baseline_dt:
                return deployment

        return None

    def wait_for_new_deployment(
        self,
        application_id: str,
        baseline_timestamp: Optional[str],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Wait for a new deployment to appear after triggering.

        This is critical to avoid the race condition where we check status before
        the deployment has been created in the system.

        Args:
            application_id: Application ID
            baseline_timestamp: Timestamp of latest deployment before trigger
            timeout: Max seconds to wait for deployment to appear

        Returns:
            The new deployment object

        Raises:
            DeploymentNotFoundError: If no new deployment appears within timeout
        """
        self.logger.info("Waiting for deployment to be created...")

        start_time = time.time()
        poll_interval = 2  # Start with 2 second polls

        while time.time() - start_time < timeout:
            deployments = self.client.get_deployments(application_id)
            new_deployment = self._find_deployment_after(deployments, baseline_timestamp)

            if new_deployment:
                deployment_id = new_deployment['deploymentId']
                elapsed = int(time.time() - start_time)
                self.logger.info(
                    f"Found new deployment: {deployment_id} (detected after {elapsed}s)"
                )
                return new_deployment

            self.logger.debug(f"No new deployment yet, waiting {poll_interval}s...")
            time.sleep(poll_interval)

        # Timeout
        raise DeploymentNotFoundError(
            f"No new deployment appeared within {timeout} seconds. "
            "The deployment might have been queued but not started yet, "
            "or the API call failed silently."
        )

    def wait_for_completion(
        self,
        application_id: str,
        deployment_id: str,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        Wait for a specific deployment to complete.

        Polls the deployment status with smart backoff and detects:
        - Instant "done" (race condition - deployment never started)
        - Stuck in "idle" (queued but not processing)
        - Failed deployments
        - Timeout

        Args:
            application_id: Application ID
            deployment_id: Specific deployment ID to track
            timeout: Max seconds to wait (default 10 minutes for builds)

        Returns:
            Final deployment object

        Raises:
            DeploymentFailedError: If deployment fails
            DeploymentTimeoutError: If deployment times out
        """
        self.logger.info(f"Tracking deployment: {deployment_id}")
        self.logger.info(f"Timeout: {timeout}s (~{timeout//60} minutes)")

        start_time = time.time()
        last_status = None
        seen_running = False
        poll_count = 0

        # Exponential backoff: 3s, 5s, 5s, 10s, 10s, 15s, 15s, 20s, 20s...
        def get_poll_interval(count: int) -> int:
            if count < 2:
                return 3
            elif count < 4:
                return 5
            elif count < 6:
                return 10
            elif count < 8:
                return 15
            else:
                return 20

        while True:
            elapsed = int(time.time() - start_time)

            # Check timeout
            if elapsed >= timeout:
                raise DeploymentTimeoutError(
                    f"Deployment {deployment_id} timed out after {timeout}s. "
                    f"Last status: {last_status}"
                )

            # Get all deployments and find ours
            deployments = self.client.get_deployments(application_id)
            deployment = next(
                (d for d in deployments if d['deploymentId'] == deployment_id),
                None
            )

            if not deployment:
                raise DeploymentNotFoundError(
                    f"Deployment {deployment_id} disappeared from deployment list"
                )

            status = deployment['status']
            error_message = deployment.get('errorMessage')

            # Log status change
            if status != last_status:
                self.logger.info(f"[{elapsed}s] Status: {status}")
                last_status = status

            # Track if we've seen the deployment actually running
            if status == 'running':
                seen_running = True

            # Check for terminal states
            if status == 'done':
                # CRITICAL FIX: Detect race condition
                # If deployment shows "done" very quickly without ever being "running",
                # we might be looking at a stale status from before the deployment started
                if elapsed < 5 and not seen_running:
                    self.logger.warning(
                        f"Deployment marked 'done' after only {elapsed}s without "
                        "entering 'running' state. This might be a race condition."
                    )

                finished_at = deployment.get('finishedAt')
                self.logger.success(
                    f"Deployment completed successfully in {elapsed}s "
                    f"(finished: {finished_at})"
                )
                return deployment

            elif status == 'error':
                error_detail = f": {error_message}" if error_message else ""
                raise DeploymentFailedError(
                    f"Deployment {deployment_id} failed{error_detail}"
                )

            elif status == 'cancelled':
                raise DeploymentFailedError(
                    f"Deployment {deployment_id} was cancelled"
                )

            # Check for stuck states
            if status == 'idle' and elapsed > 120:
                self.logger.warning(
                    f"Deployment stuck in 'idle' state for {elapsed}s. "
                    "It might be queued behind other deployments."
                )

            # Wait before next poll
            poll_count += 1
            interval = get_poll_interval(poll_count)
            self.logger.debug(
                f"[{elapsed}s] Status: {status}, next poll in {interval}s"
            )
            time.sleep(interval)

    def track_deployment(
        self,
        application_id: str,
        baseline_timestamp: Optional[str],
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        Complete deployment tracking: wait for creation, then wait for completion.

        This is the main entry point that combines both phases of tracking:
        1. Wait for the new deployment to appear in the API
        2. Track that deployment to completion

        Args:
            application_id: Application ID
            baseline_timestamp: Timestamp of latest deployment before trigger
            timeout: Total timeout in seconds (default 10 minutes)

        Returns:
            Final deployment object

        Raises:
            DeploymentNotFoundError: If deployment not found
            DeploymentFailedError: If deployment fails
            DeploymentTimeoutError: If deployment times out
        """
        # Phase 1: Wait for deployment to be created (max 30s)
        new_deployment = self.wait_for_new_deployment(
            application_id,
            baseline_timestamp,
            timeout=30
        )

        deployment_id = new_deployment['deploymentId']

        # Phase 2: Wait for completion (remaining timeout)
        return self.wait_for_completion(
            application_id,
            deployment_id,
            timeout=timeout
        )
