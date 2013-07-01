import catnap
import yaml

def parse_yaml(f):
    """Parses a YAML-based test file"""
    return catnap.Test.parse(yaml.load(f))
