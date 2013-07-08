from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import functools
import json
import sys
import base64
import requests
import requests.auth
from .compat import *

class ParseException(Exception):
    """An exception that occurrs while parsing a test specification"""

    def __init__(self, data_type, data_name, message):
        """
        :arg string data_type: The type of item that was being parsed when the
            error occurred - 'test' or 'testcase'
        :arg string data_name: The name of the test or testcase that was being
            parsed when the error occurred
        :arg string message: The error message
        """
        super(ParseException, self).__init__("%s %s: %s" % (data_type, data_name, message))

def _get_field(data_type, data, field_name, parser, required=False):
    """
    Gets/parses a field from a test/testcase
    :arg string data_type: The type of item that is being parsed - 'test' or
        'testcase'
    :arg dict data: The item that contains the field
    :arg string field_name: The name of the field to extract
    :arg function parser: The function used to parse the raw value
    """

    if field_name in data:
        # Get the field value if it exists
        value = data[field_name]
        
        if parser:
            # Parse the field value or throw an error
            try:
                value = parser(value)
            except Exception as e:
                data_name = data.get("name", "unknown")
                raise ParseException(data_type, data_name, "Could not parse field %s: %s" % (field_name, str(e)))

        return value
    elif required:
        # Throw an error if the field is required and does not exist
        data_name = data.get("name", "unknown")
        raise ParseException(data_type, data_name, "Missing required field %s" % field_name)
    else:
        # Return nothing if the field is not required and does not exist
        return None

def _auth_config_parser(config):
    """
    Parses an auth configuration. Two forms are allowed:
    * 'basic user pass' - Performs HTTP basic authentication with the
      specified username and password
    * 'digest user pass' - Performs HTTP digest authentication with the
      specified username and password

    :arg string config: The auth config string
    """
    parts = config.split()

    if len(parts) != 3:
        raise Exception(data_type, data_name, "Invalid auth config. Must specify an auth method (basic or digest) followed by the auth parameters for that method.")

    if parts[0] == "basic":
        return requests.auth.HTTPBasicAuth(parts[1], parts[2])
    elif parts[0] == "digest":
        return requests.auth.HTTPDigestAuth(parts[1], parts[2])
    else:
        raise Exception("Unknown auth method: %s" % parts[0])

def _get_file_contents(path):
    """
    Gets the contents of a specified file, ensuring that the file is properly
    closed when the function exits
    """
    with open(path, "r") as f:
        return f.read()

class TestcaseResult(object):
    """
    Model for the result of a testcase execution. This can be used in a `with`
    block so that the model catches exceptions and temporarily replaces
    stdout/stderr with a string buffer for output capture.
    """

    def __enter__(self):
        # Temporarily replace stdout/stderr with a string buffer
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr
        sys.stdout = self._captured_stdout = StringIO()
        sys.stderr = self._captured_stderr = StringIO()
        return self

    def __exit__(self, type, value, traceback):
        # Save the error
        self.error_type = type
        self.error = value
        self.error_traceback = traceback

        # Capture the stdout/stderr results
        self.stdout = self._captured_stdout.getvalue()
        self._captured_stdout.close()

        self.stderr = self._captured_stderr.getvalue()
        self._captured_stderr.close()

        # Set stdout/stderr back to their old values
        sys.stdout = self._old_stdout
        sys.stderr = self._old_stderr

        return True

    @property
    def failed(self):
        """Returns whether the testcase failed"""
        return self.error != None

class Testcase(object):
    """Model that represents a testcase specification"""

    def __init__(self, name):
        """
        Creates a new testcase
        :arg string name: The name of the testcase
        """
        self.name = name

    @classmethod
    def _choose_field(cls, testcase, data, field_type_name, **fields):
        all_fields = ((field, _get_field("testcase", data, field, parser)) for (field, parser) in fields.items())
        set_fields = [(field, value) for (field, value) in all_fields if value != None]

        if len(set_fields) > 1:
            raise ParseException("testcase", testcase.name, "More than one %s defined" % field_type_name)
        else:
            setattr(testcase, "%s_type" % field_type_name, set_fields[0][0] if set_fields else None)
            setattr(testcase, field_type_name, set_fields[0][1] if set_fields else None)

    @classmethod
    def parse(cls, data):
        """
        Parses a testcase into a model
        :arg dict data: The data to parse into a model
        """

        # Create a shortcut for extracting a field value
        field = functools.partial(_get_field, "testcase", data)

        # Get the request fields
        t = cls(field("name", str, required=True))
        t.method = field("method", lambda m: str(m).upper()) or "GET"
        t.url = field("url", str, required=True)
        t.query_params = field("query_params", dict) or {}
        t.headers = field("headers", dict) or {}
        t.auth = field("auth", _auth_config_parser)

        # Get the request body payload
        cls._choose_field(t, data, "body",
            body=lambda b: b,
            form_body=lambda b: urllib.urlencode(dict(b)),
            base64_body=lambda b: base64.b64decode(bytes(b)),
            file_body=_get_file_contents
        )

        # Set the response fields
        t.code = field("code", int)
        t.response_url = field("response_url", str)
        t.response_headers = field("response_headers", dict) or {}

        # Set the expected response body
        cls._choose_field(t, data, "response_body",
            response_body=lambda b: b,
            base64_response_body=lambda b: base64.b64decode(bytes(b)),
            file_response_body=_get_file_contents,
            json_response_body=json.loads
        )

        # Set the testcase-specified python executable code
        create_compiler = lambda field_name: functools.partial(compile, filename="<%s field of %s>" % (field_name, t.name), mode="exec")
        t.on_request = field("on_request", create_compiler("on_request"))
        t.on_response = field("on_response", create_compiler("on_response"))

        return t

class Test(object):
    """Model that represents a test"""

    def __init__(self, name):
        """
        Creates a new test
        :arg string name: The name of the test
        """
        self.name = name
        self.testcases = []

    @classmethod
    def parse(cls, data):
        """
        Parses a test into a model
        :arg dict data: The data to parse into a model
        """
        
        field = functools.partial(_get_field, "test", data)
        test = cls(field("name", str, required=True))

        for testcase_data in field("testcases", list, required=True):
            test.testcases.append(Testcase.parse(testcase_data))

        return test
