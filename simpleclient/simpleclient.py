#!/usr/bin/env python
# simpleclient - Python Simple HTTP Client.
#
# Copyright (c) 2021 nggit.
#
import sys
import socket
import ssl

if sys.version_info >= (3, 0):
    from urllib.parse import urlsplit, parse_qs, urlencode
else:
    from urlparse import urlsplit, parse_qs
    from urllib import urlencode

class Stream:
    def __init__(self, debug=False, maxredirs=-1, timeout=None):
        self._debug       = debug
        self._maxredirs   = maxredirs
        self._timeout     = timeout
        self._secure      = False
        self._url         = 'http://localhost/'
        self._host        = 'localhost'
        self._port        = 80
        self._path        = '/'
        self._sock        = None
        self._redirscount = 0
        self._request     = {
            'cookie': {},
            'headers': {'Connection': 'Connection: close'},
            'options': {'headers': {}}
        }
        self._response    = {'status': []}

    def _open(self):
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(self._timeout)

    def _close(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def setheaders(self, headers=[]):
        for header in headers:
            self._request['headers'][header[:header.index(':')].title()] = header
        return self

    def seturl(self, url):
        if not url.find('://') > 0:
            raise Exception('Invalid url or not an absolute url')
        self._url = url
        parse_url = urlsplit(url)
        if parse_url.hostname is None:
            raise Exception('Invalid host')
        else:
            self._host = parse_url.hostname
        self._secure = parse_url.scheme.lower() == 'https'
        if self._secure:
            if parse_url.port is None:
                self._port = 443
            else:
                self._port = parse_url.port
        else:
            if parse_url.port is None:
                self._port = 80
            else:
                self._port = parse_url.port
        if parse_url.path == '':
            self._path = '/'
        else:
            self._path = parse_url.path + parse_url.query
        return self

    def setmaxredirs(self, maxredirs=-1):
        self._setmaxredirs = maxredirs
        return self

    def settimeout(self, timeout=None):
        self._timeout = timeout
        return self

    def parse_cookie(self, cookie):
        cookies = {}
        for name, value in parse_qs(cookie).items():
            cookies[name.lstrip()] = value[-1]
        return cookies

    def _parse_response(self):
        self._open()
        if self._secure:
            hasattr(ssl, 'PROTOCOL_TLS') or setattr(ssl, 'PROTOCOL_TLS', ssl.PROTOCOL_SSLv23)
            context    = ssl.SSLContext(ssl.PROTOCOL_TLS)
            self._sock = context.wrap_socket(self._sock, server_hostname=self._host)
        try:
            self._sock.connect((self._host, self._port))
        except Exception:
            print("Failed to connect to '%s' port '%d'" % (self._host, self._port))
            self._close()
            sys.exit(1)
        self._sock.send(self._request['options']['message'].encode())
        self._request['options']['headers'] = {} # destroy the previous request options
        next = len(self._response)
        self._response[next] = {'headers': {}, 'header': '', 'body': ''}
        cookies  = []
        response = self._sock.makefile()
        for line in response:
            if line.rstrip() == '':
                break
            colon_pos = line.find(':')
            if not colon_pos > 0:
                self._response[next]['headers'][0] = line.rstrip()
            else:
                name  = line[:colon_pos].title()
                value = line[colon_pos:].strip(': \r\n')
                if name == 'Set-Cookie':
                    cookies += [value]
                self._response[next]['headers'][name] = value
            self._response[next]['header'] += line
        for line in response:
            self._response[next]['body'] += line
        if cookies != []:
            cookie = self.parse_cookie('; '.join(cookies))
            if 'domain' in cookie:
                domain = cookie['domain']
            else:
                domain = self._host
            if domain in self._request['cookie']:
                self._request['cookie'][domain].update(cookie)
            else:
                self._request['cookie'][domain] = cookie
        self._close()
        return self._response[next]

    def getresponse(self, number=None):
        if number is None:
            return self._response
        else:
            return self._response.get(number, {})

    def parse_status(self, status):
        self._response['status'] = status.replace('/', ' ', 1).split(None, 3)

    def getprotocol(self):
        return self._response['status'][0]

    def getprotocolversion(self):
        return self._response['status'][1]

    def getstatuscode(self):
        return self._response['status'][2]

    def getreasonphrase(self):
        return self._response['status'][3]

    def getheaders(self):
        return list(self._response.values())[-1]['headers']

    def getheader(self, header=None):
        if header is None:
            return list(self._response.values())[-1]['header']
        else:
            return list(self._response.values())[-1]['headers'].get(header)

    def getbody(self):
        return list(self._response.values())[-1]['body']

    def _realurl(self, url):
        if not url.find('://') > 0: # relative url
            path_pos = self._url.index(self._host) + len(self._host)
            if url[0] == '/':
                url = self._url[:path_pos] + url
            else:
                if not self._path.find('?') > 0:
                    path = self._path
                else:
                    path = self._path[:self._path.index('?')]
                base = self._url[:path_pos] + '/'
                if not path[path.rfind('/') + 1:].find('.') > 0:
                    base += path.lstrip('/')
                else:
                    base += path[:path.rfind('/') + 1].lstrip('/')
                url = base.rstrip('/') + '/' + url
        return url

    def request(self, method='GET', data=''):
        if method.upper() == 'POST':
            if isinstance(data, dict):
                data = urlencode(data)
                self._request['options']['headers']['Content-Type'] = 'Content-Type: application/x-www-form-urlencoded'
            else:
                if 'Content-Type' not in self._request['headers']:
                    self._request['headers']['Content-Type'] = 'Content-Type: application/x-www-form-urlencoded'
        self._request['options']['headers']['Content-Length'] = 'Content-Length: %d' % len(data)
        for domain in self._request['cookie']:
            if self._host[-len(domain):] == domain:
                self._request['options']['headers']['Cookie'] = 'Cookie: %s' % urlencode(self._request['cookie'][domain]).replace('&', '; ')
        self._request['headers']['Host'] = 'Host: %s' % self._host
        self._request['options']['headers'].update(self._request['headers'])
        self._request['options']['message'] = '%s %s HTTP/1.0\r\n%s\r\n\r\n%s' % (
                                               method, self._path, '\r\n'.join(list(self._request['options']['headers'].values())), data)
        if self._debug is True:
            print('%s----------------' % self._request['options']['message'])
        return self

    def send(self):
        if self._request['options']['headers'] == {}:
            self.request()
        response = self._parse_response()
        if 'Location' in response['headers'] and response['headers']['Location'] != self._url and (
                self._maxredirs < 0 or self._redirscount < self._maxredirs):
            self._redirscount += 1
            return (self.setheaders(['Referer: %s' % self._url])
                        .seturl(self._realurl(response['headers']['Location']))
                        .request().send())
        else:
            self.parse_status(self.getheader(0)) # last status
            self._redirscount = 0
            return self
