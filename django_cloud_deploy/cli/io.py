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
"""Class for managing console I/O."""

import abc
import contextlib
import getpass
import os
import re
import sys
import threading
import time

from progress import bar


class _ProgressBar(object):
    """A progress bar showing status of a task.

    Output of the progress bar will be like the following:
        Processing █████████████████∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙ 55%
    """

    def __init__(self, expect_time: int, message: str):
        """Constructor of the class.

        It will take "expect_time" seconds for the progress bar to go from 0%
        to 100%. If the task takes shorter than "expect time", the progress bar
        will directly go to 100%.

        Args:
            expect_time: How long the progress bar is going to run.
                (In seconds).
            message: A prefix of the progress bar showing what it is about.
        """
        self._expected_time = expect_time

        # The bar will tick every 0.5 seconds.
        self._bar = bar.ChargingBar(message, max=expect_time * 2)
        self._thread = threading.Thread(target=self._run)
        self._bar_lock = threading.Lock()

    def start(self):
        self._thread.start()

    def finish(self):
        self._finish()

    def _run(self):
        """The function to update progress bar."""
        for _ in range(self._expected_time * 2):
            self._bar_lock.acquire()

            # The progress of the bar can be modified by _finish method. This
            # part is to handle that case.
            if self._bar.progress == 1:
                self._bar_lock.release()
                return
            self._bar.next()
            self._bar_lock.release()
            time.sleep(0.5)

    def _finish(self):
        """Make progress bar go to the end.

        This is useful when the task takes shorter than the expect time to
        finish.
        """
        self._bar_lock.acquire()

        # Go to the end of progress bar.
        self._bar.goto(self._expected_time * 2)
        self._bar.finish()
        self._bar_lock.release()


class IO(abc.ABC):

    def __init__(self):
        pass

    @abc.abstractmethod
    def tell(self, *args):
        """Prints `args` to stdout.

        Args:
            args: The objects to print. For strings, the following HTML tags are
                interpreted: <b>This text in bold</b>.
        """
        pass

    @abc.abstractmethod
    def error(self, *args):
        """Prints `args` to stderr.

        Args:
            args: The objects to print. For strings, the following HTML tags are
                interpreted: <b>This text in bold</b>.
        """
        pass

    @abc.abstractmethod
    def ask(self, prompt=None):
        pass

    @abc.abstractmethod
    def getpass(self, prompt=None):
        """Prompt the user for a password and return the result."""


class ConsoleIO(IO):
    BOLD = '\033[1m'
    END = '\033[0m'

    def _replace_html_tags(self, s, f):
        if isinstance(s, str):
            bold_substitution = r'\1'
            if os.isatty(f) and os.name == 'posix':
                bold_substitution = r'{0}\1{1}'.format(self.BOLD, self.END)

            return re.sub('<b>(.*?)</b>', bold_substitution, s)
        else:
            return s

    def tell(self, *args):
        print(*(self._replace_html_tags(a, sys.stdout.fileno()) for a in args))

    def error(self, *args):
        print(
            *(self._replace_html_tags(a, sys.stdout.fileno()) for a in args),
            file=sys.stderr)

    def ask(self, prompt=None):
        return input(self._replace_html_tags(prompt, sys.stdout.fileno()))

    def getpass(self, prompt=None):
        """Prompt the user for a password and return the result."""
        return getpass.getpass(prompt)

    @contextlib.contextmanager
    def progressbar(self, expected_time: int, message: str):
        progress_bar = _ProgressBar(expected_time, message)
        try:
            progress_bar.start()
            yield
        finally:
            progress_bar.finish()


class TestIO(IO):

    def __init__(self):
        self.tell_calls = []
        self.error_calls = []
        self.answers = []
        self.ask_prompts = []
        self.passwords = []
        self.password_answers = []

    def tell(self, *args):
        self.tell_calls.append(args)

    def error(self, *args):
        self.error_calls.append(args)

    def ask(self, prompt=None):
        self.ask_prompts.append(prompt)
        return self.answers.pop(0)

    def getpass(self, prompt=None):
        """Prompt the user for a password and return the result."""
        self.passwords.append(prompt)
        return self.password_answers.pop(0)
