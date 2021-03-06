from setuptools import setup

setup(
    name = "Catnap",
    version = "0.4.5",
    description = "A script for running integration tests against RESTful/HTTP-based interfaces",
    author = "Yusuf Simonson",
    url = "http://github.com/dailymuse/catnap",
    
    packages = [
        "catnap",
    ],
    
    scripts = ["scripts/catnap"],

    install_requires = [
        "PyYAML==3.10",
        "requests==1.2.3",
        "optfn==0.4.0"
    ]
)
