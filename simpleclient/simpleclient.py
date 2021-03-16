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
    def __init__(self, debug=False, maxredirs=-1, timeout=None, close=True):
        self._debug       = debug
        self._maxredirs   = maxredirs
        self._timeout     = timeout
        self._close       = close
        self._secure      = False
        self._url         = 'http://localhost:80/'
        self._host        = 'localhost'
        self._port        = 80
        self._netloc      = 'localhost:80'
        self._referer     = ''
        self._path        = '/'
        self._sock        = None
        self._redirscount = 0
        self._request     = {
            'cookie': {},
            'headers': {'Connection': 'Connection: keep-alive'},
            'options': {'headers': {}}
        }
        self._response    = {'status': []}

    def _open(self):
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._sock.settimeout(self._timeout)
            if self._secure:
                hasattr(ssl, 'PROTOCOL_TLS') or setattr(ssl, 'PROTOCOL_TLS', ssl.PROTOCOL_SSLv23)
                context    = ssl.SSLContext(ssl.PROTOCOL_TLS)
                self._sock = context.wrap_socket(self._sock, server_hostname=self._host)
            try:
                self._sock.connect((self._host, self._port))
            except:
                print('Failed to connect to %s port %d' % (self._host, self._port))
                self.close()
                sys.exit(1)

    def close(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def setheaders(self, headers=[]):
        for header in headers:
            colon_pos = header.index(':')
            name      = header[:colon_pos].title()
            if name == 'Referer':
                self._referer = header[colon_pos:].lstrip(': ')
            self._request['headers'][name] = header
        return self

    def seturl(self, url):
        if not url.find('://') > 0:
            raise ValueError('Invalid URL or not an absolute URL')
        self._url = url
        parse_url = urlsplit(url)
        if parse_url.hostname is None:
            raise ValueError('Invalid Host')
        else:
            self._host = parse_url.hostname
        self._netloc = parse_url.netloc
        self._secure = parse_url.scheme.lower() == 'https'
        if self._secure:
            self._port = 443
        else:
            self._port = 80
        if parse_url.port is not None:
            self._port = parse_url.port
        if parse_url.path == '':
            self._path = '/'
        else:
            self._path = (parse_url.path + '?' + parse_url.query).rstrip('?')
        return self

    def setmaxredirs(self, maxredirs=-1):
        self._maxredirs = maxredirs
        return self

    def settimeout(self, timeout=None):
        self._timeout = timeout
        return self

    def parse_cookie(self, cookie):
        for name, value in parse_qs(cookie).items():
            yield name.lstrip(), value[-1]

    def _parse_response(self):
        self._sock.send(self._request['options']['message'].encode())
        next                 = len(self._response)
        self._response[next] = {'headers': {}, 'header': '', 'body': ''}
        cookies              = []
        response             = self._sock.makefile()
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
        if self._response[next]['header'] != '' and 'Location' not in self._response[next]['headers']:
            self._response[next]['body'] = response.read()
        response.close()
        if self._response[next]['header'] == '': # trigger a retry
            self.close()
            self._response[next]['headers']['Location'] = self._url
            self._url                                   = self._referer
        else:
            self._request['options']['headers'].clear() # destroy the previous request options
        if cookies != []:
            cookie = {}
            domain = self._host
            for name, value in self.parse_cookie('; '.join(cookies)):
                cookie[name] = value
                if name.lower() == 'domain':
                    domain = value
            if domain in self._request['cookie']:
                self._request['cookie'][domain].update(cookie)
            else:
                self._request['cookie'][domain] = cookie
        return self._response[next]

    def getresponse(self, number=None):
        if number is None:
            return self._response
        else:
            return self._response.get(number, {})

    def parse_status(self, status):
        self._response['status'] = (status.replace('/', ' ', 1).split(None, 3) + ['', '', '', ''])[:4]

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
            return list(self._response.values())[-1]['headers'].get(header, '')

    def getbody(self):
        return list(self._response.values())[-1]['body']

    def _realurl(self, url):
        if not url.find('://') > 0: # relative url
            path_pos = self._url.index(self._netloc) + len(self._netloc)
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
        elif method.upper() == 'HEAD':
            self.setmaxredirs(0)
        if data == '':
            if 'Content-Type' in self._request['headers']:
                del self._request['headers']['Content-Type']
        else:
            self._request['options']['headers']['Content-Length'] = 'Content-Length: %d' % len(data)
        for domain in self._request['cookie']:
            if self._host[-len(domain):] == domain:
                self._request['options']['headers']['Cookie'] = 'Cookie: %s' % urlencode(self._request['cookie'][domain]).replace('&', '; ')
                break
        self._request['headers']['Host'] = 'Host: %s' % self._host
        self._request['options']['headers'].update(self._request['headers'])
        self._request['options']['message'] = '%s %s HTTP/1.0\r\n%s\r\n\r\n%s' % (
                                               method, self._path, '\r\n'.join(list(self._request['options']['headers'].values())), data)
        if self._debug is True:
            print('%s\r\n----------------' % self._request['options']['message'].rstrip())
        return self

    def send(self):
        if urlsplit(self._referer).netloc != self._netloc:
            self.close()
        self._open()
        if self._request['options']['headers'] == {}:
            self.request()
        response = self._parse_response()
        if 'Location' in response['headers'] and response['headers']['Location'] != self._url and (
                self._maxredirs < 0 or self._redirscount < self._maxredirs):
            self._redirscount += 1
            return (self.setheaders(['Referer: %s' % self._url])
                        .seturl(self._realurl(response['headers']['Location']))
                        .send())
        else:
            self.parse_status(self.getheader(0)) # last status
            if self._close:
                self.close()
            self._redirscount = 0
            return self.setheaders(['Referer: %s' % self._url])
