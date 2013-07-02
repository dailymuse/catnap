import catnap
import requests

def execute_testcase(testcase, session=None, request_options={}):
    """
    Executes a testcase
    """

    # Construct a new session if one has not been provided, whose scope will#
    # only last through this testcase
    if not session:
        session = requests.Session()

    # Set a default User-Agent (this can be overriden by user options)
    headers = {
        "User-Agent": "Catnap %s" % catnap.version
    }

    headers.update(testcase.headers)

    # Build the request
    request = requests.Request(
        testcase.method, testcase.url,
        headers=headers,
        data=testcase.body,
        params=testcase.query_params,
        auth=testcase.auth
    ).prepare()

    # Create a context for sharing with testcase-specified python code
    context = dict(request=request, response=None, session=session, testcase=testcase)

    # Within this `with` block, stdout/stderr will be replaced and buffered
    # to a string for later output. Errors will be caught for display.
    with catnap.TestcaseResult() as result:
        # Run the `on_request` code if specified
        if testcase.on_request:
            exec testcase.on_request in context

        # Get the response
        response = session.send(request, **request_options)
        context["response"] = response

        # Validate the response code
        if testcase.code:
            assert response.status_code == testcase.code, "Expected code %s, but got code %s" % (testcase.code, response.status_code)

        # Validate the response (redirected) URL
        if testcase.response_url:
            assert response.url == testcase.response_url, "Expected to be redirected to URL %s, but got %s" % (testcase.response_url, response.url)

        # Validate the response headers
        for key, value in testcase.response_headers.iteritems():
            actual_value = response.headers.get(key)
            assert actual_value != None, "Expected header %s is missing" % key
            assert actual_value == value, "Expected header %s to be %s, but got %s" % (key, value, actual_value)

        # Validate the response body
        if testcase.response_body:
            actual_value = response.content

            if testcase.response_body_parser:
                try:
                    actual_value = testcase.response_body_parser(actual_value)
                except Exception, e:
                    raise Exception("Could not parse the response body: %s" % e.message)

            assert actual_value == testcase.response_body, "Unexpected response body"

        # Run the `on_response` code if specified
        if testcase.on_response:
            exec testcase.on_response in context

    return result
