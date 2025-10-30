"""
CLI commands for dokdeploy tool.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional

from src.config import DokployConfig, ConfigError, load_config
from src.logger import DeployLogger
from src.dokploy_client import DokployClient, DokployAPIError
from src.deployment_tracker import (
    DeploymentTracker,
    DeploymentNotFoundError,
    DeploymentFailedError,
    DeploymentTimeoutError
)


def cmd_init(args) -> int:
    """Initialize config file."""
    config_path = Path(args.config) if args.config else DokployConfig.DEFAULT_CONFIG_PATH

    if config_path.exists() and not args.force:
        print(f"Config file already exists: {config_path}")
        print("Use --force to overwrite")
        return 1

    try:
        created_path = DokployConfig.create_template(config_path)
        print(f"✓ Created config file: {created_path}")
        print(f"\nNext steps:")
        print(f"1. Edit the config file: {created_path}")
        print(f"2. Add your Dokploy URL and API token")
        print(f"3. Add your applications")
        print(f"4. Run: dokdeploy list")
        return 0
    except Exception as e:
        print(f"Error creating config: {e}", file=sys.stderr)
        return 1


def cmd_list(args) -> int:
    """List configured applications."""
    try:
        config = load_config(args.config)

        print(f"Dokploy URL: {config.dokploy_url}")
        print(f"Config file: {config.config_path}")
        print(f"\nConfigured applications ({len(config.apps)}):")
        print()

        for name, app in config.apps.items():
            print(f"  {name}")
            print(f"    ID:      {app.id}")
            print(f"    Name:    {app.app_name}")
            print(f"    Wait:    {app.wait_for_completion}")
            print(f"    Restart: {app.restart}")
            print()

        return 0

    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1


def cmd_deploy(args) -> int:
    """Deploy one or more applications."""
    try:
        config = load_config(args.config)
        logger = DeployLogger(debug=args.debug)

        # Determine which apps to deploy
        if args.all:
            app_names = config.list_apps()
        else:
            app_names = args.apps

        if not app_names:
            print("Error: Specify app names or use --all", file=sys.stderr)
            return 1

        # Validate all apps exist before deploying
        for app_name in app_names:
            try:
                config.get_app(app_name)
            except ConfigError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1

        # Deploy each app
        failed = []
        succeeded = []

        for app_name in app_names:
            app = config.get_app(app_name)

            # Override with CLI flags if provided
            wait = args.wait if args.wait is not None else app.wait_for_completion
            no_wait = args.no_wait if args.no_wait else False
            if no_wait:
                wait = False

            restart = args.restart if args.restart else app.restart
            debug = args.debug if args.debug else app.debug

            logger.debug_mode = debug

            print(f"\n{'='*60}")
            print(f"Deploying: {app_name}")
            print(f"{'='*60}")

            try:
                result = deploy_app(
                    config=config,
                    app=app,
                    wait_for_completion=wait,
                    restart=restart,
                    logger=logger
                )
                if result == 0:
                    succeeded.append(app_name)
                else:
                    failed.append(app_name)

            except KeyboardInterrupt:
                logger.warning(f"\nDeployment of {app_name} cancelled by user")
                failed.append(app_name)
                break

            except Exception as e:
                logger.error(f"Unexpected error deploying {app_name}: {e}")
                failed.append(app_name)

        # Summary
        print(f"\n{'='*60}")
        print("Deployment Summary")
        print(f"{'='*60}")
        print(f"✓ Succeeded: {len(succeeded)}")
        if succeeded:
            for name in succeeded:
                print(f"  - {name}")
        print(f"✗ Failed: {len(failed)}")
        if failed:
            for name in failed:
                print(f"  - {name}")

        return 0 if not failed else 1

    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1


def deploy_app(
    config: DokployConfig,
    app,
    wait_for_completion: bool,
    restart: bool,
    logger: DeployLogger
) -> int:
    """Deploy a single application."""
    try:
        logger.info(f"Application: {app.app_name} ({app.id})")
        logger.info(f"Wait for completion: {wait_for_completion}")
        logger.info(f"Restart after deploy: {restart}")

        # Initialize client and tracker
        client = DokployClient(config.dokploy_url, config.auth_token, logger)
        tracker = DeploymentTracker(client, logger)

        # Get baseline deployment
        logger.info("Getting current deployment state...")
        deployments = client.get_deployments(app.id)

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

        # Trigger deployment
        client.deploy(app.id)

        # If not waiting, exit now
        if not wait_for_completion:
            logger.info("Deployment triggered. Not waiting for completion.")
            logger.warning(
                "⚠️  Not verifying deployment succeeded. "
                "Use --wait or set wait_for_completion: true in config."
            )
            return 0

        # Track deployment to completion
        with logger.group("Tracking deployment progress"):
            try:
                final_deployment = tracker.track_deployment(
                    application_id=app.id,
                    baseline_timestamp=baseline_timestamp,
                    timeout=600
                )

                deployment_id = final_deployment['deploymentId']
                logger.success(f"Deployment verified: {deployment_id}")

            except DeploymentNotFoundError as e:
                logger.error(str(e))
                return 1

            except DeploymentFailedError as e:
                logger.error(str(e))
                return 1

            except DeploymentTimeoutError as e:
                logger.error(str(e))
                return 1

        # Optional restart
        if restart:
            logger.info("Restart requested, stopping and starting application...")

            with logger.group("Restarting application"):
                try:
                    import time

                    client.stop(app.id)
                    logger.info("Waiting 5 seconds for clean shutdown...")
                    time.sleep(5)

                    client.start(app.id)
                    logger.info("Waiting 10 seconds for application to start...")
                    time.sleep(10)

                    application = client.get_application(app.id)
                    app_status = application.get('applicationStatus', 'unknown')

                    if app_status in ('done', 'running'):
                        logger.success(f"Application restarted successfully (status: {app_status})")
                    else:
                        logger.warning(
                            f"Application restarted but status is '{app_status}'. "
                            "Please verify manually."
                        )

                except DokployAPIError as e:
                    logger.error(f"Restart failed: {e}")
                    return 1

        logger.success(f"✓ Deployment completed successfully for {app.app_name}")
        return 0

    except DokployAPIError as e:
        logger.error(f"Dokploy API error: {e}")
        return 1


def cmd_status(args) -> int:
    """Show application status."""
    try:
        config = load_config(args.config)
        logger = DeployLogger(debug=args.debug)

        for app_name in args.apps:
            app = config.get_app(app_name)

            print(f"\n{app_name} ({app.app_name}):")
            print(f"  ID: {app.id}")

            try:
                client = DokployClient(config.dokploy_url, config.auth_token, logger)
                application = client.get_application(app.id)

                status = application.get('applicationStatus', 'unknown')
                print(f"  Status: {status}")

                # Show recent deployments
                deployments = client.get_deployments(app.id)
                if deployments:
                    latest = deployments[0]
                    print(f"  Latest deployment:")
                    print(f"    ID:       {latest['deploymentId']}")
                    print(f"    Status:   {latest['status']}")
                    print(f"    Created:  {latest['createdAt']}")
                    if latest.get('finishedAt'):
                        print(f"    Finished: {latest['finishedAt']}")

            except DokployAPIError as e:
                print(f"  Error: {e}")

        return 0

    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1


def cmd_history(args) -> int:
    """Show deployment history."""
    try:
        config = load_config(args.config)
        logger = DeployLogger(debug=args.debug)

        app = config.get_app(args.app)

        print(f"\nDeployment history for {args.app} ({app.app_name}):")

        try:
            client = DokployClient(config.dokploy_url, config.auth_token, logger)
            deployments = client.get_deployments(app.id)

            if not deployments:
                print("  No deployments found")
                return 0

            # Show last N deployments
            limit = args.limit or 10
            for i, dep in enumerate(deployments[:limit]):
                print(f"\n  [{i+1}] {dep['deploymentId']}")
                print(f"      Status:   {dep['status']}")
                print(f"      Created:  {dep['createdAt']}")
                if dep.get('startedAt'):
                    print(f"      Started:  {dep['startedAt']}")
                if dep.get('finishedAt'):
                    print(f"      Finished: {dep['finishedAt']}")
                if dep.get('errorMessage'):
                    print(f"      Error:    {dep['errorMessage']}")

            if len(deployments) > limit:
                print(f"\n  ... and {len(deployments) - limit} more")
                print(f"  Use --limit to see more")

        except DokployAPIError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        return 0

    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1


def cmd_config(args) -> int:
    """Config file operations."""
    if args.subcommand == 'show':
        return cmd_config_show(args)
    elif args.subcommand == 'validate':
        return cmd_config_validate(args)
    else:
        print(f"Unknown config subcommand: {args.subcommand}", file=sys.stderr)
        return 1


def cmd_config_show(args) -> int:
    """Show configuration."""
    try:
        config = load_config(args.config)

        print(f"Config file: {config.config_path}")
        print(f"\nDokploy:")
        print(f"  URL: {config.dokploy_url}")
        print(f"  Token: {'*' * 20 if config.auth_token else '(not set)'}")

        print(f"\nDefaults:")
        for key, value in config.defaults.items():
            print(f"  {key}: {value}")

        print(f"\nApplications ({len(config.apps)}):")
        for name, app in config.apps.items():
            print(f"  - {name}")

        return 0

    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1


def cmd_config_validate(args) -> int:
    """Validate configuration."""
    try:
        config = load_config(args.config)
        issues = config.validate()

        if not issues:
            print(f"✓ Configuration is valid ({config.config_path})")
            return 0
        else:
            print(f"✗ Configuration has issues:")
            for issue in issues:
                print(f"  - {issue}")
            return 1

    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='dokdeploy',
        description='Deploy applications to Dokploy from the command line'
    )

    parser.add_argument(
        '-c', '--config',
        type=Path,
        help=f'Config file path (default: {DokployConfig.DEFAULT_CONFIG_PATH})'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # init command
    init_parser = subparsers.add_parser('init', help='Initialize config file')
    init_parser.add_argument('-f', '--force', action='store_true', help='Overwrite existing config')

    # list command
    subparsers.add_parser('list', help='List configured applications')

    # deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy application(s)')
    deploy_parser.add_argument('apps', nargs='*', help='Application name(s) to deploy')
    deploy_parser.add_argument('-a', '--all', action='store_true', help='Deploy all applications')
    deploy_parser.add_argument('--wait', action='store_true', help='Wait for deployment to complete')
    deploy_parser.add_argument('--no-wait', action='store_true', help='Do not wait for deployment')
    deploy_parser.add_argument('--restart', action='store_true', help='Restart after deployment')
    deploy_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    # status command
    status_parser = subparsers.add_parser('status', help='Show application status')
    status_parser.add_argument('apps', nargs='+', help='Application name(s)')
    status_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    # history command
    history_parser = subparsers.add_parser('history', help='Show deployment history')
    history_parser.add_argument('app', help='Application name')
    history_parser.add_argument('-n', '--limit', type=int, help='Number of deployments to show (default: 10)')
    history_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    # config command
    config_parser = subparsers.add_parser('config', help='Configuration operations')
    config_subparsers = config_parser.add_subparsers(dest='subcommand', help='Config commands')
    config_subparsers.add_parser('show', help='Show configuration')
    config_subparsers.add_parser('validate', help='Validate configuration')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to command handlers
    commands = {
        'init': cmd_init,
        'list': cmd_list,
        'deploy': cmd_deploy,
        'status': cmd_status,
        'history': cmd_history,
        'config': cmd_config,
    }

    handler = commands.get(args.command)
    if handler:
        try:
            return handler(args)
        except KeyboardInterrupt:
            print("\n\nCancelled by user", file=sys.stderr)
            return 130
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
