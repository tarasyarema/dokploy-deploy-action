"""
Dokploy API client for triggering and monitoring deployments.
"""

import requests
from typing import Dict, List, Optional, Any
from .logger import DeployLogger


class DokployAPIError(Exception):
    """Raised when Dokploy API returns an error."""
    pass


class DokployClient:
    """Client for interacting with Dokploy API."""

    def __init__(self, base_url: str, api_key: str, logger: DeployLogger):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'x-api-key': api_key
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request to Dokploy API with error handling."""
        url = f"{self.base_url}{endpoint}"

        self.logger.debug(f"{method} {url}")
        if 'json' in kwargs:
            self.logger.debug(f"Request body: {kwargs['json']}")

        try:
            response = self.session.request(method, url, **kwargs)

            self.logger.debug(f"Response status: {response.status_code}")
            if response.text:
                self.logger.debug(f"Response body: {response.text[:500]}")

            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            error_msg = f"API request failed: {e}"
            if e.response is not None and e.response.text:
                error_msg += f" - {e.response.text}"
            self.logger.error(error_msg)
            raise DokployAPIError(error_msg) from e

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {e}"
            self.logger.error(error_msg)
            raise DokployAPIError(error_msg) from e

    def deploy(self, application_id: str) -> None:
        """
        Trigger deployment for an application.

        Note: This endpoint returns 200 OK but no deployment ID in the response body.
        You must poll deployment/all to find the newly created deployment.

        Args:
            application_id: The Dokploy application ID

        Raises:
            DokployAPIError: If the API request fails
        """
        self.logger.info(f"Triggering deployment for application: {application_id}")

        self._make_request(
            'POST',
            '/api/application/deploy',
            json={'applicationId': application_id}
        )

        self.logger.info("Deployment triggered successfully")

    def deploy_compose(self, compose_id: str) -> None:
        """
        Trigger deployment for a compose service.

        Note: This endpoint returns 200 OK but no deployment ID in the response body.
        You must poll deployment.allByCompose to find the newly created deployment.

        Args:
            compose_id: The Dokploy compose ID

        Raises:
            DokployAPIError: If the API request fails
        """
        self.logger.info(f"Triggering deployment for compose: {compose_id}")

        self._make_request(
            'POST',
            '/api/compose.deploy',
            json={'composeId': compose_id}
        )

        self.logger.info("Compose deployment triggered successfully")

    def get_deployments(self, application_id: str) -> List[Dict[str, Any]]:
        """
        Get all deployments for an application, sorted by creation time (newest first).

        Args:
            application_id: The Dokploy application ID

        Returns:
            List of deployment objects with fields:
            - deploymentId: Unique deployment ID
            - status: 'idle', 'running', 'done', 'error', 'cancelled'
            - createdAt: ISO timestamp when deployment was created
            - startedAt: ISO timestamp when deployment started
            - finishedAt: ISO timestamp when deployment finished
            - errorMessage: Error message if status is 'error'
            - logPath: Path to deployment logs

        Raises:
            DokployAPIError: If the API request fails
        """
        self.logger.debug(f"Fetching deployments for application: {application_id}")

        response = self._make_request(
            'GET',
            f'/api/deployment/all?applicationId={application_id}'
        )

        deployments = response.json()
        self.logger.debug(f"Found {len(deployments)} deployments")

        return deployments

    def get_compose_deployments(self, compose_id: str) -> List[Dict[str, Any]]:
        """
        Get all deployments for a compose service, sorted by creation time (newest first).

        Args:
            compose_id: The Dokploy compose ID

        Returns:
            List of deployment objects with same structure as application deployments

        Raises:
            DokployAPIError: If the API request fails
        """
        self.logger.debug(f"Fetching deployments for compose: {compose_id}")

        response = self._make_request(
            'GET',
            f'/api/deployment.allByCompose?composeId={compose_id}'
        )

        deployments = response.json()
        self.logger.debug(f"Found {len(deployments)} compose deployments")

        return deployments

    def get_application(self, application_id: str) -> Dict[str, Any]:
        """
        Get application details.

        Args:
            application_id: The Dokploy application ID

        Returns:
            Application object with fields like:
            - applicationStatus: Overall application status
            - deployments: Array of recent deployments

        Raises:
            DokployAPIError: If the API request fails
        """
        self.logger.debug(f"Fetching application details: {application_id}")

        response = self._make_request(
            'GET',
            f'/api/application/one?applicationId={application_id}'
        )

        return response.json()

    def get_compose(self, compose_id: str) -> Dict[str, Any]:
        """
        Get compose service details.

        Args:
            compose_id: The Dokploy compose ID

        Returns:
            Compose object with fields like:
            - composeStatus: Overall compose status
            - deployments: Array of recent deployments

        Raises:
            DokployAPIError: If the API request fails
        """
        self.logger.debug(f"Fetching compose details: {compose_id}")

        response = self._make_request(
            'GET',
            f'/api/compose.one?composeId={compose_id}'
        )

        return response.json()

    def reload(self, application_id: str, app_name: str) -> None:
        """
        Reload an application.

        Args:
            application_id: The Dokploy application ID
            app_name: The application name

        Raises:
            DokployAPIError: If the API request fails
        """
        self.logger.info(f"Triggering reload for application: {app_name}")

        self._make_request(
            'POST',
            '/api/application/reload',
            json={
                'applicationId': application_id,
                'appName': app_name
            }
        )

        self.logger.info("Reload triggered successfully")

    def stop(self, application_id: str) -> None:
        """
        Stop an application.

        Args:
            application_id: The Dokploy application ID

        Raises:
            DokployAPIError: If the API request fails
        """
        self.logger.info(f"Stopping application: {application_id}")

        self._make_request(
            'POST',
            '/api/application/stop',
            json={'applicationId': application_id}
        )

        self.logger.info("Application stopped successfully")

    def start(self, application_id: str) -> None:
        """
        Start an application.

        Args:
            application_id: The Dokploy application ID

        Raises:
            DokployAPIError: If the API request fails
        """
        self.logger.info(f"Starting application: {application_id}")

        self._make_request(
            'POST',
            '/api/application/start',
            json={'applicationId': application_id}
        )

        self.logger.info("Application started successfully")

    def stop_compose(self, compose_id: str) -> None:
        """
        Stop a compose service.

        Args:
            compose_id: The Dokploy compose ID

        Raises:
            DokployAPIError: If the API request fails
        """
        self.logger.info(f"Stopping compose: {compose_id}")

        self._make_request(
            'POST',
            '/api/compose.stop',
            json={'composeId': compose_id}
        )

        self.logger.info("Compose stopped successfully")

    def start_compose(self, compose_id: str) -> None:
        """
        Start a compose service.

        Args:
            compose_id: The Dokploy compose ID

        Raises:
            DokployAPIError: If the API request fails
        """
        self.logger.info(f"Starting compose: {compose_id}")

        self._make_request(
            'POST',
            '/api/compose.start',
            json={'composeId': compose_id}
        )

        self.logger.info("Compose started successfully")
