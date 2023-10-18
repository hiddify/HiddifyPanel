from json import dumps

try:
    from urllib import urlencode, unquote
    from urlparse import urlparse, parse_qsl, ParseResult
except ImportError:
    # Python 3 fallback
    from urllib.parse import (
        urlencode, unquote, urlparse, parse_qsl, ParseResult
    )


import webbrowser

class IssueUrl:
    def __init__(self, options):
        
        repoUrl = None
        
        self.opts = options

        if "repoUrl" in self.opts:
            repoUrl = self.opts["repoUrl"]
            
            try:
                del self.opts["user"]
                del self.opts["repo"]
            except:
                pass

        elif "user" in self.opts and "repo" in options:
            
            try:
                del self.opts["repoUrl"]
            except:
                pass

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

            try:
                value = self.opts[type]
            except:
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