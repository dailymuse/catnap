from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import catnap
import yaml

def parse_yaml(f):
    """Parses a YAML-based test file"""
    return catnap.Test.parse(yaml.load(f))
