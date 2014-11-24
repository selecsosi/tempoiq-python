import requests
from requests.auth import HTTPBasicAuth
import urlparse
import urllib


def make_url_args(params):
    """Utility function for constructing a URL query string from a dictionary
    of parameters.  The dictionary's values can be of various types: lists,
    tuples, dictionaries, strings, or None.

    :param dict params: the key-value pairs to construct a query string from
    :rtype: string"""

    p = []
    for key, value in params.iteritems():
        if isinstance(value, (list, tuple)):
            for v in value:
                p.append((key, v))
        elif isinstance(value, dict):
            for k, v in value.items():
                p.append(('%s[%s]' % (key, k), v))
        elif isinstance(value, bool):
            p.append((key, str(value).lower()))
        elif value is None:
            continue
        else:
            p.append((key, str(value)))
    return urllib.urlencode(p).encode("UTF-8")


def merge_headers(h1, h2):
    return dict(h1.items() + h2.items())


def media_types(accept, content):
    return {
        'Accept': ','.join(accept),
        'Content-Type': content
    }


def media_type(media_resource, media_version, suffix='json'):
    return 'application/prs.tempoiq.%s.%s+%s' % (
        media_resource, media_version, suffix)


class HTTPEndpoint(object):
    """Represents an HTTP endpoint for accessing a REST API.  Provides
    utility methods for GET, POST, PUT, and DELETE requests. Do not explicitly
    call the methods on this class, use the :class:`tempoiq.client.Client`
    class instead.

    :param string base_url: the base URL for the endpoint
    :param string key: the API key for the endpoint
    :param string secret: the API secret for the endpoint"""

    def __init__(self, base_url, key, secret):
        if base_url.endswith('/'):
            self.base_url = base_url + 'v2/'
        else:
            #in case people use their own, it really has to end in a
            #slash so the urljoins will work properly
            self.base_url = base_url + '/v2/'

        self.headers = {
            'User-Agent': 'tempoiq-python/%s' % "1.0.1",
            'Accept-Encoding': 'gzip'
        }
        self.auth = HTTPBasicAuth(key, secret)
        self.pool = requests.session()
        for p in ['http://', 'https://']:
            adapter = requests.adapters.HTTPAdapter()
            self.pool.mount(p, adapter)

    def post(self, url, body, headers={}):
        """Perform a POST request to the given resource with the given
        body.  The "url" argument will be joined to the base URL this
        object was initialized with.

        :param string url: the URL resource to hit
        :param string body: the POST body for the request
        :rtype: requests.Response object"""

        to_hit = urlparse.urljoin(self.base_url, url)
        merged = merge_headers(self.headers, headers)
        resp = self.pool.post(to_hit, data=body, auth=self.auth,
                              headers=merged)
        return resp

    def get(self, url, body='', headers={}):
        """Perform a GET request to the given resource with the given URL.  The
        "url" argument will be joined to the base URL this object was
        initialized with.

        :param string url: the URL resource to hit
        :rtype: requests.Response object"""

        to_hit = urlparse.urljoin(self.base_url, url)
        merged = merge_headers(self.headers, headers)
        resp = self.pool.get(to_hit, data=body, auth=self.auth,
                             headers=merged)
        return resp

    def delete(self, url, body='', headers={}):
        """Perform a DELETE request to the given resource with the given.  The
        "url" argument will be joined to the base URL this object was
        initialized with.

        :param string url: the URL resource to hit
        :rtype: requests.Response object"""

        to_hit = urlparse.urljoin(self.base_url, url)
        merged = merge_headers(self.headers, headers)
        resp = self.pool.delete(to_hit, data=body, auth=self.auth,
                                headers=merged)
        return resp

    def put(self, url, body, headers={}):
        """Perform a PUT request to the given resource with the given
        body.  The "url" argument will be joined to the base URL this
        object was initialized with.

        :param string url: the URL resource to hit
        :param string body: the PUT body for the request
        :rtype: requests.Response object"""

        to_hit = urlparse.urljoin(self.base_url, url)
        merged = merge_headers(self.headers, headers)
        resp = self.pool.put(to_hit, data=body, auth=self.auth,
                             headers=merged)
        return resp
