# catnap #

Catnap is a simple command line utility that allows you to write integration
tests for HTTP-based interfaces via declarative YAML specifications. When a
check must be conducted that involves complex logic or falls outside of the
scope of what is provided, catnap provides a parachute: you can extend tests
with python code to perform further validation.

## Getting Started ##

To install, simply run `pip install catnap`.

Then run the script: `catnap <test file> [options]`

Options:

* `--verbose`: Enables verbose output. Failures will print the full stack
  trace for better context.
* `--timeout=10`: Sets the timeout for a request in seconds. Defaults to 10.
* `--cookies`: Save cookies across requests. By default, cookies are ignored.
* `--allow-redirects`: Automatically follow redirects.
* `--verify-ssl-certs`: Enables verification of SSL certs.
* `--http-proxy`: Enables an HTTP proxy to use, e.g. `http://10.10.1.10:3128`
* `--https-proxy`: Enables an HTTPS proxy to use.

## Test specifications ##

Tests are specified in YAML files. Here's an example test specification:

    name: github
    testcases:
      # A very basic request
      - name: homepage
        url: http://github.com
        code: 200
        # Check to make sure we were redirected to https
        response_url: https://github.com/
        response_headers:
          content-type: text/html; charset=utf-8

      # Demostrates the use of some more advanced features: auth, on_request and
      # on_response
      - name: create a new gist with bad auth
        method: POST
        url: https://api.github.com/gists
        # Authenticate using HTTP basic with username foo and password bar
        auth: basic foo bar
        response_headers:
          content-type: application/json; charset=utf-8
        on_request: 'print "on_request:", request, response'
        on_response: |
          json = response.json()

          if response.status_code == 401:
            assert json["message"] == "Bad credentials", ""
          elif response.status_code == 403:
            assert json["message"] == "Max number of login attempt exceeded", ""
          else:
            raise Exception("Unexpected status code: %s" % response.status_code)

Test files specify a name (in this example, `github`), and a list of testcases. Each testcase will make a request and validate the response against the spec.

### Testcase properties ###

#### Request properties ####

* `name` (required): Specifies the name of the testcase.
* `method` (defaults to `GET`): the HTTP method to use in the request.
* `url` (required): The URL to request.
* `query_params`: A map of query parameter keys to values that will be added to the URL.
* `headers`: A map of HTTP header names to values to be used in the request.
* `auth`: An authentication configuration for the request. Either of the form `basic user pass` for HTTP basic authentication, or `digest user pass` for HTTP digest.

#### Request body properties ####

You can specify one (or none) of the following per testcase:

* `body`: A body to send with the request.
* `form_body`: A map of form keys to values. This mapping will be encoded and send in the body as POST parameters.
* `base64_body`: A base64-encoded body to send with the request. Useful for sending binary data.
* `file_body`: A path to a file to send as the request body. Useful for requests with large bodies.

#### Response properties ####

* `code`: The expected HTTP return code.
* `response_url`: The expected URL from a response, assuming `--allow-redirects` is enabled.

#### Response body properties ####

You can specify one (or none) of the following per testcase:

* `response_body`: The expected response body, specified in plaintext.
* `base64_response_body`: The expected response body as encoded in base64 (useful for verifying binary responses).
* `file_response_body`: The path to a file that contains the expected response body (useful for responses with large bodies).
