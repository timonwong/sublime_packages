# -*- coding: utf-8 -*-

import json
from semver import SemVer
import re


def test_json_file():
    with open('packages.json') as f:
        json.load(f)


def semver_compat(v):
    if isinstance(v, SemVer):
        return str(v)

    # Allowing passing in a dict containing info about a package
    if isinstance(v, dict):
        if not hasattr(v, 'version'):
            return 0
        v = v['version']

    # We prepend 0 to all date-based version numbers so that developers
    # may switch to explicit versioning from GitHub/BitBucket
    # versioning based on commit dates.
    #
    # When translating dates into semver, the way to get each date
    # segment into the version is to treat the year and month as
    # minor and patch, and then the rest as a numeric build version
    # with four different parts. The result looks like:
    # 0.2012.11+10.31.23.59
    date_match = re.match('(\d{4})\.(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})$', v)
    if date_match:
        v = '0.%s.%s+%s.%s.%s.%s' % date_match.groups()

    # This handles version that were valid pre-semver with 4+ dotted
    # groups, such as 1.6.9.0
    four_plus_match = re.match('(\d+\.\d+\.\d+)[T\.](\d+(\.\d+)*)$', v)
    if four_plus_match:
        v = '%s+%s' % (four_plus_match.group(1), four_plus_match.group(2))

    # Semver must have major, minor, patch
    elif re.match('^\d+$', v):
        v += '.0.0'
    elif re.match('^\d+\.\d+$', v):
        v += '.0'
    return v


def test_package():
    with open('packages.json') as f:
        j = json.load(f)
        for package in j['packages']:
            for platform in package['platforms']:
                assert platform in ('*', 'windows', 'linux', 'osx')
                archives = package['platforms'][platform]
                for archive in archives:
                    # Test version
                    SemVer(semver_compat(archive['version']))
