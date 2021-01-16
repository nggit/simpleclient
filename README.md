# simpleclient
simpleclient "Python Simple HTTP Client" is a simple [guzzle](https://github.com/guzzle/guzzle)-like library built on top of The Standard Python Library. Unlike guzzle, simpleclient is smaller, and not full of features. It is compatible with Python 2.x and 3.x. There is also a [php-simple-client](https://github.com/nggit/php-simple-client) written in PHP.

## Install
```
pip install simpleclient
```
## Quick Start
```python
import simpleclient

client = simpleclient.Stream()
```
## Simple GET
**Send a GET Request**
```python
client.seturl('https://www.google.com/') # required to set an url
client.send()
```
**Display Responses**
```python
print(client.getheader())
# HTTP/1.1 200 OK
# Date: Mon, 14 Jan 2020 14:14:48 GMT
# Expires: -1
# Cache-Control: private, max-age=0
# Content-Type: text/html; charset=UTF-8
# ...

print(client.getheader(0))
# HTTP/1.1 200 OK

print(client.getheader('Content-Type'))
# text/html; charset=UTF-8

print(client.getbody())
# <!doctype html>...</html>
```
## Custom Requests
Custom requests using the request() method.
```python
client.seturl('https://www.google.com/') # required to set an url
client.request('HEAD')
client.send()
```
You can also provide a payload, for example, for a POST request. The payload can be a dictionary, or a string. It will automatically send a 'Content-Type: application/x-www-form-urlencoded' header. You can set it manually with the setheaders() method for other types required.
```python
client.request('POST', {'user': 'myusername', 'pass': 'mypassword'})
```
## Setting Headers To Be Sent
Setting Headers must be done before calling request() and send() method.
```python
client.setheaders([
    'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
    'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language: en-US,en;q=0.5'
])
```
## Common
```python
print(client.getprotocol())        # HTTP
print(client.getprotocolversion()) # 1.1
print(client.getstatuscode())      # 200
print(client.getreasonphrase())    # OK
```
And other features to hack like the getresponse() method.
