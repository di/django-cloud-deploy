# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A module handles crash of the tool."""

import os
import platform
import subprocess
import sys
import traceback
import urllib.parse
import webbrowser

import jinja2

from django_cloud_deploy.cli import io


# TODO: Add an issue label for issues reported by users
_REQUEST_URL_TEMPLATE = (
    ('https://github.com/GoogleCloudPlatform/django-cloud-deploy/issues/new?'
     'body={}'))


with open(os.path.join(os.path.dirname(__file__), 'template',
                       'issue_template.txt')) as f:
    _ISSUE_TEMPLATE = f.read()


def handle_crash(err: Exception, command: str,
                 console: io.IO = io.ConsoleIO()):
    """The tool's crashing handler.

    Args:
        err: The exception get thrown.
        command: The command causing the exception to get thrown.
        console: Object to use for user I/O.
    """

    # TODO: Only handle crashes caused by our code, not user's code.
    console.tell(
        'django-cloud-deploy crashed with ({}): {}'.format(
            type(err).__name__, err))

    ans = console.ask(
        'Would you like to file a bug against Django Cloud Deploy?\n'
        'If you want, we will open a browser to direct you to the\n'
        'tool\'s Github repo. The bug will include information about\n'
        'your environment but you can remove any information that you\n'
        'don\'t want to share [y/N]: ')

    while ans.lower() not in ['y', 'n']:
        ans = console.ask('Please answer "y" or "N": ')

    if ans.lower() == 'y':
        _create_issue(command)


def _create_issue(command: str):
    """Open browser to create a issue on the package's Github repo.

    Args:
        command: What command we want to create issue for.
    """
    template_env = jinja2.Environment()
    try:
        gcloud_version = subprocess.check_output(
            ['gcloud', 'info', '--format=value(basic.version)'],
            universal_newlines=True).rstrip()
    except subprocess.CalledProcessError:
        gcloud_version = 'Not installed or not on PATH'

    try:
        docker_version = subprocess.check_output(
            ['docker', '--version'], universal_newlines=True).rstrip()
    except subprocess.CalledProcessError:
        docker_version = 'Not installed or not on PATH'

    try:
        cloud_sql_proxy_version = subprocess.check_output(
            ['cloud_sql_proxy', '--version'], universal_newlines=True).rstrip()
    except subprocess.CalledProcessError:
        cloud_sql_proxy_version = 'Not installed or not on PATH'

    # TODO: Add django-cloud-deploy version
    template = template_env.from_string(_ISSUE_TEMPLATE)
    options = {
        'command': command,
        'gcloud_version': gcloud_version,
        'docker_version': docker_version,
        'cloud_sql_proxy_version': cloud_sql_proxy_version,
        'python_version': sys.version.replace('\n', ' '),
        'traceback': traceback.format_exc(),
        'platform': platform.platform(),
    }
    content = template.render(options)
    url = urllib.parse.quote(_REQUEST_URL_TEMPLATE.format(content), safe='/:?=')
    webbrowser.open(url)
