#!/usr/bin/python3
""" admin.py - core functions to administer the jobengine.
      Includes:
         Config Class
"""
# import os
import getpass
import sys
import logging
# import urllib2
import requests
from requests.auth import HTTPBasicAuth
import rmxml


def geturl(input_url, content='text'):
    """
    Inputs a valid URL and returns a requests object.
    for compatibility reasons, the default return is the response text.
    If you want the whole object, include a 'content='object'' statement,
    and you can use the whole response object for looking at
    headers, status_code, cookies, history, etc.
    """
    try:
        # response = urllib2.urlopen(input_url)
        response = requests.get(input_url)
        # http_data = response.read()
        # response.close()
    # except urllib2.URLError as urlerror:
    #    return "urllib2 URLError {0}".format(urlerror)
    except StandardError as error:
        return "standard Error {0}".format(error)
    if content == 'text':
        return response.text
    return response


class Config(object):
    """creates a configuration object"""

    def __init__(self, config=None, **kwargs):
        self.config = config
        self.version = None
        self.logfile = None
        self.loglevel = None
        self.interval = None
        self.job = None
        self.keyfile = None

        mykwargs = kwargs
        if config is not None:
            self.read()
        elif kwargs:
            self.simple(mykwargs)
        else:
            self.input()

    def read(self):
        "Reads the credential file and builds auth object"
        def _strip(content, field):
            extract = [field, ":", " ", "\n", "\t"]
            for item in extract:
                if item in content:
                    newline = content.replace(item, "")
                    content = newline
                else:
                    pass
            return content

        with open(self.config, "r") as auth:
            valid_options = self.__dict__
            while True:
                newline = auth.readline()
                if not newline:
                    break
                elif newline.startswith("#"):
                    pass
                else:
                    for key in valid_options:
                        if key in newline:
                            setattr(self, key, _strip(newline, key))
                        else:
                            pass
        return

    def input(self):
        "Manually configures authentication"
        self.job = input("job file: ")
        self.loglevel = input("Log Level: ")
        self.logfile = input("logfile name: ")
        self.logfile = input("logfile name: ")
        self.interval = input("Interval (secodns): ")
        self.keyfile = input("Key File: ")
        return

    def simple(self, data):
        "configures via kwargs"
        # print ("simple configurator!")
        # print ("data is: {0}".format(data))
        for value in data:
            # print ("Value is {0}".format(value))
            if value == 'logfile':
                self.logfile = data[value]
                # print ('self.logfile set to {0}'.format(self.logfile))
            elif value == 'loglevel':
                self.loglevel = data[value]
            elif value == 'interval':
                self.interval = int(data[value])
            elif value == 'job':
                self.job = data[value]
            elif value == 'keyfile':
                self.keyfile = data[value]
        return


class KeySecret(object):
    """A class that handles credentials that exist as key-secret pairs.
    This can include username, password, etc, but useful for storing
    AWS credentials and such in a file.
    Can be invoked in the following ways:
    KeySecret(source='source_credential_file', key='keydata',
        secret='secredata')
    where source_credential_file is a file which contains a key and secret
    in foramt:
    key: xxxxxxxxxxxxxx
    secret: xxxxxxxxxxx
       where xxxxx... refers to the actual characters of each.

    if a credential file is not passed, you can pass credentails explicitly
    by stating:
    KeySecret(key='keydata', secret='secredata')
    or - by specifying nothing, int he keySecret() call, you will be prompted
    by input to enter a key and secret.
    """

    def __init__(self, source=None, **kwargs):
        self.cfile = source
        self.key = None
        self.secret = None
        self.service = None

        mykwargs = kwargs
        if self.cfile is not None:
            self.read()
        elif kwargs:
            self.simple(mykwargs)
        else:
            self.input()

    def read(self):
        "Reads the credential file and builds auth object"
        def _strip(content, field):
            extract = [field, ":", " ", "\n", "\t"]
            for item in extract:
                if item in content:
                    newline = content.replace(item, "")
                    content = newline
                else:
                    pass
            return content

        with open(self.cfile, "r") as auth:
            valid_options = self.__dict__
            while True:
                newline = auth.readline()
                if not newline:
                    break
                elif newline.startswith("#"):
                    pass
                else:
                    for key in valid_options:
                        if key in newline:
                            setattr(self, key, _strip(newline, key))
                        else:
                            pass
        return

    def input(self):
        "Manually configures authentication"
        valid_options = self.__dict__
        for key in valid_options:
            setattr(self, key, input("{0}: ".format(key)))
        return

    def simple(self, data):
        "configures via kwargs"
        valid_options = self.__dict__
        for value in data:
            for key in valid_options:
                if value == key:
                    setattr(self, key, data[value])
        return


def credentials(cfile, result=None):
    """gets the stored credentials from a given filename to pass to
       a job."""
    with open(cfile, 'r') as myfile:
        while True:
            newline = myfile.readline()
            if not newline:
                break
            elif newline.startswith("#"):
                pass
            elif 'key' in newline:
                result = sanitize(newline, 'key')
            else:
                pass
    return result


def logging_config(loglevel):
    """Configures logging options including:
         filename:  log filename including path and appender
         level:   log level as:
              INFO, WARN, ERROR, CRITICAL  """

    level_list = {'debug': logging.DEBUG, 'info': logging.INFO,
                  'warn': logging.WARN, 'error': logging.ERROR,
                  'critical': logging.CRITICAL}

    for key in level_list:
        if loglevel.lower() == key:
            return level_list[key]

    return logging.NOTSET


def sanitize(content, field):
    """Strips characters from a string"""
    extract = [field, ":", " ", "\n", "\t"]
    for item in extract:
        if item in content:
            newline = content.replace(item, "")
            content = newline
        else:
            pass
    return content


class API(object):
    """ Alternate API Call Class for Remote Manager"""

    def __init__(self, auth=None):
        self.auth = None
        self.username = None
        self.password = None
        self.cluster = 'test.idigi.com'
        self.service = None
        self.url = None
        self.cursor = None

        if auth:
            self.set_auth(auth)

    def set_auth(self, auth):
        """passes auth from an Auth Object """
        self.username = auth.username
        self.password = auth.password
        self.cluster = auth.cluster

    def check(self):
        """used to perform checks on API values """
        print (self.__dict__)

    def get(self, **kwargs):
        """ performs the get request """
        def _page_cursor(opener, url, headers, data):
            requestedsize = int(headers["<requestedSize>"])
            resultsize = int(headers["<resultSize>"])
            self.cursor = str(headers["<pageCursor>"])
            source_url = url
            while resultsize == requestedsize:
                headers = {}
                url = source_url + "&pageCursor={0}".format(
                    str(self.cursor))
                try:
                    feed = opener.open(url).read()
                    headers = rmxml.extract_headers(feed)
                    new_data = rmxml.delete_headers(feed)
                    data = data + new_data
                except urllib2.URLError:
                    sys.exit("Can't connect to {0}.".format(url))
                self.cursor = str(headers["<pageCursor>"])
                requestedsize = int(headers["<requestedSize>"])
                resultsize = int(headers["<resultSize>"])
            self.cursor = str(headers["<pageCursor>"])
            return headers, data

        def _remaining_size(opener, url, headers, data):
            remaining = 1000
            source_url = url
            start = 0
            remaining = int(headers['<remainingSize>'])
            while remaining != 0:
                start = start + 1000
                headers = {}
                if "?" in source_url:
                    url = source_url + "&start={0}".format(str(start))
                else:
                    url = source_url + "?start={0}".format(str(start))
                try:
                    feed = opener.open(url).read()
                    headers = rmxml.extract_headers(feed)
                    new_data = rmxml.delete_headers(feed)
                    data = data + new_data
                    remaining = int(headers['<remainingSize>'])
                except urllib2.URLError:
                    sys.exit("Can't connect to {0}.".format(url))
            return headers, data

        def _feed_remaining(opener, url, extract):
            if self.cursor is not None:
                cursor_url = url = url + "&pageCursor={0}".format(
                    str(self.cursor))
                feed = opener.open(cursor_url).read()
            else:
                feed = opener.open(url).read()
            headers = rmxml.extract_headers(feed)
            data = rmxml.delete_headers(feed)
            if "<remainingSize>" in headers:
                _remaining_size(opener, url, headers, data)
            elif "<pageCursor>" in headers:
                _page_cursor(opener, url, headers, data)
            if extract == 'dict':
                return_data = {'headers': headers, 'data': data}
            else:
                head = rmxml.rebuild_headers(headers)
                return_data = rmxml.rebuild_xml(head, data)
            return return_data

        extract = 'dict'
        for value in kwargs:
            # setattr(self, kwargs[value])
            if value == 'service':
                self.service = kwargs[value]
            elif value == 'extract':
                extract = kwargs[value]
        # _check_requirements(self.service, self.cluster)
        api_addr = "https://" + self.cluster + self.service
        self.url = api_addr
        pswd_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pswd_mgr.add_password(None, api_addr, self.username,
                              self.password)
        auth_handler = urllib2.HTTPBasicAuthHandler(pswd_mgr)
        opener = urllib2.build_opener(auth_handler)
        urllib2.install_opener(opener)
        feed = _feed_remaining(opener, api_addr, extract)
        return feed

    def post(self, **kwargs):
        """api post method """
        payload = None
        for value in kwargs:
            if value == 'payload':
                payload = kwargs[value]
            else:
                setattr(self, value, kwargs[value])
        api_addr = "https://" + self.cluster + self.service
        self.url = api_addr
        # if payload is not None:
        #    print (payload)
        # pswd_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        # pswd_mgr.add_password(None, api_addr, self.username,
        #                      self.password)
        # auth_handler = urllib2.HTTPBasicAuthHandler(pswd_mgr)
        # opener = urllib2.build_opener(auth_handler)
        # request = urllib2.Request(url=self.url, data=payload,
        #                           headers=headers)
        # response = opener.open(request)
        # return_response = response.read()
        headers = {'Content-Type': 'application/xml'}
        response = requests.post(self.url, auth=HTTPBasicAuth(self.username,
                                                              self.password),
                                 data=payload, headers=headers)
        return response.text


class AuthObject(object):
    """creates an authentication object"""

    def __init__(self, authfile=None, **kwargs):
        self.file = authfile
        self.cluster = None
        self.username = None
        self.password = None

        mykwargs = kwargs
        if authfile is not None:
            self.read()
        elif kwargs:
            self.simple(mykwargs)
        else:
            self.input()

    def read(self):
        "Reads the credential file and builds auth object"
        def _strip(content, field):
            valid_options = [field, ":", " ", "\n", "\t"]
            for item in valid_options:
                if item in content:
                    newline = content.replace(item, "")
                    content = newline
                else:
                    pass
            return content

        with open(self.file, "r") as auth:
            valid_options = self.__dict__
            while True:
                newline = auth.readline()
                if not newline:
                    break
                elif newline.startswith("#"):
                    pass
                else:
                    for key in valid_options:
                        if key in newline:
                            setattr(self, key, str(_strip(newline, key)))
                        else:
                            pass
        return

    def input(self):
        "Manually configures authentication"
        for key in self.__dict__:
            if key == 'password':
                setattr(self, key, getpass.getpass(key + ": "))
            elif key == 'file':
                pass
            else:
                setattr(self, key, input(key + ": "))
        return

    def show(self):
        """used to perform checks on API values """
        print (self.__dict__)

    def simple(self, data):
        "configures via kwargs"
        for key in self.__dict__:
            for k in data:
                if k == key:
                    setattr(self, key, data[k])
        return


class RMsvcGen(object):
    """Generates a services url call by specifying parameters"""

    def __init__(self, **kwargs):
        self.service = None
        self.uid = None
        self.customer = None
        self.group = None
        self.attributes = {}
        self.condition = {}

        mykwargs = kwargs
        print (mykwargs)

    def get(self, **kwargs):
        """returns a webservice object """
        # webservice = "this is a web service"
        mykwargs = kwargs
        for item in mykwargs:
            if 'service' in mykwargs:
                self.service = mykwargs[item]

    def define(self, **kwargs):
        """returns a webservice object """
        # webservice = "this is a web service"
        mykwargs = kwargs
        for item in mykwargs:
            if 'service' in mykwargs:
                self.service = mykwargs[item]


class RMObject(object):
    """Generates a generic Remote Manager data object"""

    def __init__(self, *args, **kwargs):
        if kwargs:
            self.__dict__.update(kwargs)
        if args:
            self.define(*args)

    def define(self, args):
        """creates attributes from args."""
        for attribute in args:
            setattr(self, attribute, args[attribute])
        return

    def fromdict(self, dictionary):
        """creates attributes from args."""
        for k in dictionary:
            setattr(self, k, dictionary[k])
        return

    def length(self):
        """returns the number of attributes """
        return len(self.__dict__)

    def show(self):
        """used to perform checks on API values """
        print (self.__dict__)
        return

    def set(self, **kwargs):
        """sets a key and value to attribute """
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return
