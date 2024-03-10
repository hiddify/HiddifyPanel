from typing import List
from strenum import StrEnum
from flask import current_app
import subprocess
import os


class Command(StrEnum):
    apply = 'apply'
    install = 'install'
    # reinstall = 'reinstall'
    update = 'update'
    status = 'status'
    restart_services = 'restart-services'
    temporary_short_link = 'temporary-short-link'
    temporary_access = 'temporary-access'
    update_usage = 'update-usage'
    get_cert = 'get-cert'
    apply_users = 'apply-users'
    update_wg_usage = 'update-wg-usage'


def commander(command: Command, run_in_background=True, **kwargs: str | int) -> str | None:
    """
    Run the commander based on the given command type.
    Args:
        command: The type of command to run.
        run_in_background: Whether to run the command in the background.
        **kwargs: Additional arguments to pass to the commander. Accepts the following:
                  url, slug, period for the temporary-short-link command.
                  port for the temporary-access command.
                  domain for the get-cert command
    """
    base_cmd: List[str] = [
        'sudo',
        os.path.join(
            current_app.config['HIDDIFY_CONFIG_PATH'], 'common/commander.py')
    ]

    if command == Command.apply:
        base_cmd.append('apply')
    elif command == Command.install:
        base_cmd.append('install')
    elif command == Command.update:
        base_cmd.append('update')
    elif command == Command.status:
        base_cmd.append('status')
    elif command == Command.restart_services:
        base_cmd.append('restart-services')
    elif command == Command.apply_users:
        base_cmd.append('apply-users')
    elif command == Command.temporary_short_link:
        url = str(kwargs.get('url', ''))
        slug = str(kwargs.get('slug', ''))
        period = kwargs.get('period', '')

        if not url or not slug:
            raise Exception("Invalid input passed to the run_commander function for temporary-short-link command")

        base_cmd.append('temporary-short-link')
        base_cmd.extend(['--url', url, '--slug', slug])
        if period:
            base_cmd.extend(['--period', str(period)])
    elif command == Command.temporary_access:
        port = str(kwargs.get('port'))
        if not port or not port.isnumeric():
            raise Exception("Invalid input passed to the run_commander function for temporary-access command")

        base_cmd.append('temporary-access')
        base_cmd.extend(['--port', port])
    elif command == Command.update_usage:
        base_cmd.append('update-usage')
    elif command == Command.get_cert:
        domain = str(kwargs.get('domain'))
        if not domain:
            raise Exception("Invalid input passed to the run_commander function for get-cert command")
        base_cmd.extend(['get-cert', '--domain', domain])
    elif command == Command.update_wg_usage:
        base_cmd.append('update-wg-usage')
    else:
        raise Exception('WTF is happening!')
    if run_in_background:
        subprocess.Popen(base_cmd, cwd=str(current_app.config['HIDDIFY_CONFIG_PATH']), start_new_session=True)
    else:
        return subprocess.check_output(base_cmd, cwd=str(current_app.config['HIDDIFY_CONFIG_PATH'])).decode()
