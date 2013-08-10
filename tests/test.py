import json
import re


def test_json_file():
    with open('packages.json') as f:
        json.load(f)
