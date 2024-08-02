
from urllib.parse import (
    urlencode, unquote, urlparse, parse_qsl, ParseResult
)
import webbrowser
from flask import g, request, render_template
from sys import version as python_version
from platform import platform
from json import dumps
from flask import g, request, render_template

import hiddifypanel
from hiddifypanel.models.config import hconfig
from hiddifypanel.models.config_enum import ConfigEnum


class __IssueUrl:
    def __init__(self, options):

        repoUrl = None

        self.opts = options

        if "repoUrl" in self.opts:
            repoUrl = self.opts["repoUrl"]

            try:
                del self.opts["user"]
                del self.opts["repo"]
            except BaseException:
                pass

        elif "user" in self.opts and "repo" in options:
            if repoUrl in self.opts:
                del self.opts["repoUrl"]

            repoUrl = "https://github.com/{0}/{1}".format(self.opts["user"], self.opts["repo"])
        else:
            raise KeyError('You need to specify either the `repoUrl` option or both the `user` and `repo` options')

        self.url = "{0}/issues/new".format(repoUrl)

        self.types = [
            'body', 'title', 'labels', 'template', 'milestone', 'assignee', 'projects'
        ]

    def add_url_params(self, url, params):
        """ Add GET params to provided URL being aware of existing.

        :param url: string of target URL
        :param params: dict containing requested params to be added
        :return: string with updated URL

        >> url = 'http://stackoverflow.com/test?answers=true'
        >> new_params = {'answers': False, 'data': ['some','values']}
        >> add_url_params(url, new_params)
        'http://stackoverflow.com/test?data=some&data=values&answers=false'

        Source: https://stackoverflow.com/a/25580545/3821823
        """
        # Unquoting URL first so we don't loose existing args
        url = unquote(url)
        # Extracting url info
        parsed_url = urlparse(url)
        # Extracting URL arguments from parsed URL
        get_args = parsed_url.query
        # Converting URL arguments to dict
        parsed_get_args = dict(parse_qsl(get_args))
        # Merging URL arguments dict with new params
        parsed_get_args.update(params)

        # Bool and Dict values should be converted to json-friendly values
        # you may throw this part away if you don't like it :)
        parsed_get_args.update(
            {k: dumps(v) for k, v in parsed_get_args.items()
             if isinstance(v, (bool, dict))}
        )

        # Converting URL argument to proper query string
        encoded_get_args = urlencode(parsed_get_args, doseq=True)
        # Creating new parsed result object based on provided with new
        # URL arguments. Same thing happens inside of urlparse.
        new_url = ParseResult(
            parsed_url.scheme, parsed_url.netloc, parsed_url.path,
            parsed_url.params, encoded_get_args, parsed_url.fragment
        ).geturl()

        return new_url

    def get_url(self):

        url = self.url

        for type in self.types:
            value = self.opts.get(type)
            if value is None:
                continue
            if type == "labels" or type == "projects":
                if not isinstance(value, list):
                    err = "The {0} option should be an array".format(type)
                    raise TypeError(err)

                value = ",".join(map(str, value))
                self.opts[type] = value

        self.url = self.add_url_params(url, self.opts)

        return self.url

    def opn(self):
        webbrowser.open(self.get_url(), 1)

# region private functions


def __generate_github_issue_link(title: str, issue_body: str) -> str:
    opts = {
        "user": 'hiddify',
        "repo": 'Hiddify-Manager',
        "title": title,
        "body": issue_body,
    }
    issue_link = str(__IssueUrl(opts).get_url())
    return str(issue_link)


def __github_issue_details() -> dict:
    details = {
        'hiddify_version': f'{hiddifypanel.__version__}',
        'python_version': f'{python_version}',
        'os_details': f'{platform()}',
        'user_agent': request.user_agent
    }
    return details


def __remove_sensetive_data_from_github_issue_link(issue_link: str):
    from hiddifypanel.auth import current_account
    if current_account.uuid:
        issue_link = issue_link.replace(f'{current_account.uuid}', '*******************')

    issue_link = issue_link.replace(request.host, '**********')
    issue_link = issue_link.replace(hconfig(ConfigEnum.proxy_path), '**********')
    issue_link = issue_link.replace(hconfig(ConfigEnum.proxy_path_admin), '**********')
    issue_link = issue_link.replace(hconfig(ConfigEnum.proxy_path_client), '**********')
    return issue_link


def __remove_unrelated_traceback_details(stacktrace: str) -> str:
    lines = stacktrace.splitlines()
    if len(lines) < 1:
        return ""

    output = ''
    skip_next_line = False
    for i, line in enumerate(lines):
        if i == 0:
            output += line + '\n'
            continue
        if skip_next_line:
            skip_next_line = False
            continue
        if line.strip().startswith('File'):
            if 'hiddify' in line.lower():
                output += line + '\n'
                if len(lines) > i + 1:
                    output += lines[i + 1] + '\n'
            skip_next_line = True

    return output

# endregion


def generate_github_issue_link_for_500_error(error, traceback: str, remove_sensetive_data: bool = True, remove_unrelated_traceback_datails: bool = True) -> str:

    if remove_unrelated_traceback_datails:
        traceback = __remove_unrelated_traceback_details(traceback)

    issue_details = __github_issue_details()

    issue_body = render_template('github_issue_body.j2', issue_details=issue_details, error=error, traceback=traceback)

    # Create github issue link
    issue_link = __generate_github_issue_link(
        f"Internal server error: {error.name if hasattr(error,'name') and error.name != None and error.name else 'Unknown'}", issue_body)

    if remove_sensetive_data:
        issue_link = __remove_sensetive_data_from_github_issue_link(issue_link)

    return issue_link


def generate_github_issue_link_for_admin_sidebar() -> str:

    issue_body = render_template('github_issue_body.j2', issue_details=__github_issue_details())

    # Create github issue link
    issue_link = __generate_github_issue_link('Please fill the title properly', issue_body)
    return issue_link
