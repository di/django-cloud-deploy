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

import traceback
import webbrowser

from django_cloud_deploy.cli import io


_REQUEST_URL_TEMPLATE = (
    ('https://github.com/GoogleCloudPlatform/django-cloud-deploy/issues/new?'
     'body={}'))

_ISSUE_TEMPLATE = 'bar'


def handle_crash(err: Exception, console: io.IO = io.ConsoleIO()):
    console.tell(
        'django-cloud-deploy crashed with ({}): {}'.format(
            type(err).__name__, err))

    ans = console.ask(
        'Would you like to file a bug against Django Cloud Deploy? If you '
        'want, we will open a browser to direct you to the tool\'s Github '
        'repo. The bug will include information about your environment but you '
        'can remove any information that you don\'t want to share [y/N]: ')

    while ans.lower() not in ['y', 'n']:
        ans = console.ask('Please answer "y" or "N": ')

    if ans.lower() == 'y':
        _create_issue(_ISSUE_TEMPLATE)


def _create_issue(content: str):
    url = _REQUEST_URL_TEMPLATE.format(content)
    webbrowser.open(url)
