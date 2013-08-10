#!/usr/bin/env python
import os
import platform
import subprocess
import json
from string import Template


# Get every package.json file from packages
def get_package_files(packages):
    system = platform.system()
    if system == 'Windows':
        st2_packages_dir = os.path.expandvars(
            '${APPDATA}\\Sublime Text 2\\Packages')
    elif system == 'Darwin':
        st2_packages_dir = '~/Library/Application Support/Sublime Text 2/Packages'
    else:
        st2_packages_dir = '~/.config/sublime-text-2/Packages'
    package_files = [
        os.path.join(st2_packages_dir, package, 'package.json')
        for package in packages
    ]
    return package_files


def ensure_version_string(version):
    [int(x) for x in version.split('.')]


def get_package_json_information(package_file):
    # Parsing package.json, get params
    with open(package_file, "r") as f:
        package_json = json.loads(f.read())
        name = package_json["name"]
        description = package_json["description"]
        author = package_json["author"]
        homepage = package_json["homepage"]
        details = package_json["details"]
        repo = package_json["repo"]
        return {
            "name": name,
            "description": description,
            "author": author,
            "homepage": homepage,
            "details": details,
            "repo": repo
        }


def build_releases_json_string(repo):
    template_platform = Template("""
                {
                    "sublime_text": "*",
                    "details": "https://github.com/timonwong/$repo/tags"
                }""")
    json_platforms = [
        template_platform.substitute(repo=repo)
    ]
    return ",".join(json_platforms)


def build_packages_json_file(packages):
    package_files = get_package_files(packages)
    # Writing
    template_main = Template("""
        {
            "name": "$name",
            "description": "$description",
            "author": "$author",
            "homepage": "$homepage",
            "details": "$details",
            "releases": [$releases_json_string
            ]
        }""")

    packages_json = []
    for package_file in package_files:
        try:
            package_json_info = get_package_json_information(package_file)
            releases_json_string = build_releases_json_string(
                package_json_info["repo"]
            )
            info = dict(package_json_info)
            packages_json.append(template_main.substitute(
                releases_json_string=releases_json_string, **info
            ))
        except:
            import traceback
            traceback.print_exc()
    return ",".join(packages_json)

if __name__ == "__main__":
    import sys
    packages = None

    with open('package_list.txt', 'r') as f:
        packages = []
        for package in f.read().strip().split('\n'):
            package = package.strip()
            if package.startswith('#'):
                continue
            packages.append(package)

    if packages is None:
        sys.stderr.write('No package defined in package_list.txt\n')
        sys.exit(1)

    with open('packages.json', 'w') as f:
        f.write("""{
    "schema_version": "2.0",
    "packages": [""")
        f.write(build_packages_json_file(packages))
        f.write("""
    ]
}""")
