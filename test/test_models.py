import unittest
import catnap
import requests.auth

class TestModelTest(unittest.TestCase):
    def test_missing_name(self):
        self.assertRaises(catnap.ParseException, catnap.Test.parse, {"testcases": []})

    def test_missing_testcases(self):
        self.assertRaises(catnap.ParseException, catnap.Test.parse, {"name": "foo"})

    def test_valid(self):
        test = catnap.Test.parse({
            "name": "test",
            "testcases": [{
                "name": "minimal test",
                "url": "http://www.google.com",
            }, {
                "name": "complex test",
                "method": "POST",
                "url": "http://www.google.com",
                "query_params": { "hello": "world" },
                "headers": { "foo": "bar" },
                "auth": "basic user pass",
                "form_body": { "form_key": "form_value" },

                "code": 200,
                "response_url": "http://www.google.com?redirect",
                "response_headers": { "foo": "baz" },
                "base64_response_body": "aGVsbG8=",
                "on_request": "import sys; sys.stdout.write('request')",
                "on_response": "import sys; sys.stdout.write('response')",
            }]
        })

        self.assertEqual(test.name, "test")
        self.assertEqual(len(test.testcases), 2)

        t1 = test.testcases[0]

        self.assertEqual(t1.name, "minimal test")
        self.assertEqual(t1.method, "GET")
        self.assertEqual(t1.url, "http://www.google.com")
        self.assertEqual(t1.query_params, {})
        self.assertEqual(t1.headers, {})
        self.assertEqual(t1.auth, None)
        self.assertEqual(t1.body, None)
        self.assertEqual(t1.code, None)
        self.assertEqual(t1.response_url, None)
        self.assertEqual(t1.response_headers, {})
        self.assertEqual(t1.response_body, None)
        self.assertEqual(t1.on_request, None)
        self.assertEqual(t1.on_response, None)

        t2 = test.testcases[1]

        self.assertEqual(t2.name, "complex test")
        self.assertEqual(t2.method, "POST")
        self.assertEqual(t2.url, "http://www.google.com")
        self.assertEqual(t2.query_params, { "hello": "world" })
        self.assertEqual(t2.headers, { "foo": "bar" })
        self.assertEqual(t2.auth.username, "user")
        self.assertEqual(t2.auth.password, "pass")
        self.assertEqual(t2.body, "form_key=form_value")
        self.assertEqual(t2.code, 200)
        self.assertEqual(t2.response_url, "http://www.google.com?redirect")
        self.assertEqual(t2.response_headers, { "foo": "baz" })
        self.assertEqual(t2.response_body, "hello")
        self.assertNotEqual(t2.on_request, None)
        self.assertNotEqual(t2.on_response, None)

class TestcaseModelTest(unittest.TestCase):
    def build_testcase(self, **kwargs):
        data = {
            "name": "foo",
            "url": "http://www.google.com",
        }

        data.update(kwargs)
        return catnap.Testcase.parse(data)

    def test_name(self):
        testcase = self.build_testcase()
        self.assertEqual(testcase.name, "foo")
        self.assertRaises(catnap.ParseException, catnap.Testcase.parse, {"url": "foo"})

    def test_method(self):
        testcase = self.build_testcase(method="get")
        self.assertEqual(testcase.method, "GET")
        self.assertRaises(catnap.ParseException, catnap.Testcase.parse, {"method": None})

    def test_url(self):
        testcase = self.build_testcase()
        self.assertEqual(testcase.url, "http://www.google.com")
        self.assertRaises(catnap.ParseException, catnap.Testcase.parse, {"name": "foo"})

    def test_query_params(self):
        testcase = self.build_testcase(query_params={"hello": "world"})
        self.assertEqual(testcase.query_params, {"hello": "world"})
        self.assertRaises(catnap.ParseException, self.build_testcase, query_params=None)

    def test_headers(self):
        testcase = self.build_testcase(headers={"hello": "world"})
        self.assertEqual(testcase.headers, {"hello": "world"})
        self.assertRaises(catnap.ParseException, self.build_testcase, headers=None)

    def test_basic_auth(self):
        testcase = self.build_testcase(auth="basic user pass")
        self.assertTrue(isinstance(testcase.auth, requests.auth.HTTPBasicAuth))
        self.assertEqual(testcase.auth.username, "user")
        self.assertEqual(testcase.auth.password, "pass")

    def test_digest_auth(self):
        testcase = self.build_testcase(auth="digest user pass")
        self.assertTrue(isinstance(testcase.auth, requests.auth.HTTPDigestAuth))
        self.assertEqual(testcase.auth.username, "user")
        self.assertEqual(testcase.auth.password, "pass")

    def test_bad_auth(self):
        self.assertRaises(catnap.ParseException, self.build_testcase, auth="unknown user pass")

    def test_body(self):
        testcase = self.build_testcase(body="body test")
        self.assertEqual(testcase.body, "body test")

    def test_form_body(self):
        testcase = self.build_testcase(form_body={"hello": "world", "foo": "bar"})
        self.assertTrue(testcase.body in ["hello=world&foo=bar", "foo=bar&hello=world"])
        self.assertRaises(catnap.ParseException, self.build_testcase, form_body="invalidbody")

    def test_base64_body(self):
        testcase = self.build_testcase(base64_body="aGVsbG8=")
        self.assertEqual(testcase.body, "hello")
        self.assertRaises(catnap.ParseException, self.build_testcase, base64_body="invalid base64 string")

    def test_file_body(self):
        testcase = self.build_testcase(file_body="./test/static/sample.txt")
        self.assertEqual(testcase.body, "hello from a sample text file")
        self.assertRaises(catnap.ParseException, self.build_testcase, file_body="./test/nonfile.txt")

    def test_invalid_multibody(self):
        self.assertRaises(catnap.ParseException, self.build_testcase, body="plaintext body", file_body="./test/nonfile.txt")

    def test_valid_code(self):
        testcase = self.build_testcase(code="400")
        self.assertEqual(testcase.code, 400)

    def test_invalid_code(self):
        self.assertRaises(catnap.ParseException, self.build_testcase, code=None)

    def test_response_body(self):
        testcase = self.build_testcase(response_body="body test")
        self.assertEqual(testcase.response_body, "body test")

    def test_response_url(self):
        testcase = self.build_testcase(response_url="foobar")
        self.assertEqual(testcase.response_url, "foobar")
        self.assertRaises(catnap.ParseException, catnap.Testcase.parse, {"name": "foo", "response_url": None})

    def test_response_headers(self):
        testcase = self.build_testcase(response_headers={"hello": "world"})
        self.assertEqual(testcase.response_headers, {"hello": "world"})
        self.assertRaises(catnap.ParseException, self.build_testcase, response_headers=None)

    def test_base64_response_body(self):
        testcase = self.build_testcase(base64_response_body="aGVsbG8=")
        self.assertEqual(testcase.response_body, "hello")
        self.assertRaises(catnap.ParseException, self.build_testcase, base64_response_body="invalid base64 string")

    def test_file_response_body(self):
        testcase = self.build_testcase(file_response_body="./test/static/sample.txt")
        self.assertEqual(testcase.response_body, "hello from a sample text file")

        self.assertRaises(catnap.ParseException, self.build_testcase, file_response_body="./test/nonfile.txt")

    def test_invalid_response_multibody(self):
        self.assertRaises(catnap.ParseException, self.build_testcase, response_body="plaintext body", file_response_body="./test/nonfile.txt")

    def test_valid_on_request(self):
        testcase = self.build_testcase(on_request="import sys; sys.stdout.write('hi')")
        self.assertNotEqual(testcase.on_request, None)

    def test_invalid_on_request(self):
        self.assertRaises(catnap.ParseException, self.build_testcase, on_request="!!!")

    def test_valid_on_response(self):
        testcase = self.build_testcase(on_response="import sys; sys.stdout.write('hi')")
        self.assertNotEqual(testcase.on_response, None)

    def test_invalid_on_response(self):
        self.assertRaises(catnap.ParseException, self.build_testcase, on_response="!!!")

if __name__ == "__main__":
    unittest.main()
