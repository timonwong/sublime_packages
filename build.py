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
        st2_packages_dir = os.path.expandvars('${APPDATA}\\Sublime Text 2\\Packages')
    elif system == 'Darwin':
        st2_packages_dir = '~/Library/Application Support/Sublime Text 2/Packages'
    else:
        st2_packages_dir = '~/.config/sublime-text-2/Packages'
    package_files = [
        os.path.join(st2_packages_dir, package, 'package.json')
        for package in packages
    ]
    return package_files


def shell_execute(args, working_dir):
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=working_dir)


def get_package_git_information(package_file):
    package_dir = os.path.dirname(package_file)
    # Get the latest version information, base on the tag
    proc_git_tag = shell_execute(['git', 'describe', '--abbrev=0', '--tags'], package_dir)
    last_tag = proc_git_tag.communicate()[0].strip()
    # Assumes that the tag is following this format: v1.0.2
    last_version = last_tag[1:]
    # Get date
    proc_git_log = shell_execute(
        ['git', 'log', '--pretty=format:%ci', '-1', last_tag], package_dir)
    last_modified = proc_git_log.communicate()[0].strip()
    last_modified = last_modified[:19]
    if (last_tag == "" or last_version == ""):
        raise Exception("No Git Version Information")
    return {
        'last_tag': last_tag,
        'last_version': last_version,
        'last_modified': last_modified,
    }


def get_package_json_information(package_file):
    # Parsing package.json, get params
    with open(package_file, "r") as f:
        package_json = json.loads(f.read())
        name = package_json["name"]
        description = package_json["description"]
        author = package_json["author"]
        homepage = package_json["homepage"]
        repo = package_json["repo"]
        platforms = package_json["platforms"]
        return {"name": name, \
                "description": description, \
                "author": author, \
                "homepage": homepage, \
                "repo": repo, \
                "platforms": platforms}


def build_platforms_json_string(package_git_information, platforms, repo):
    template_platform = Template("""
                "$platform": [
                    {
                        "version": "$last_version",
                        "url": "https://github.com/timonwong/$repo/archive/$last_tag.zip"
                    }
                ]""")
    json_platforms = [
        template_platform.substitute(platform=platform, repo=repo, **package_git_information)
        for platform in platforms
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
            "last_modified": "$last_modified",
            "platforms": {$platform_json_string
            }
        }""")

    packages_json = []
    for package_file in package_files:
        try:
            package_json_info = get_package_json_information(package_file)
            package_git_info = get_package_git_information(package_file)
            platforms_json_string = build_platforms_json_string(
                package_git_info,
                package_json_info["platforms"],
                package_json_info["repo"]
            )
            info = dict(package_json_info, **package_git_info)
            packages_json.append(template_main.substitute(
                platform_json_string=platforms_json_string, **info
            ))
        except:
            import traceback
            traceback.print_exc()
    return ",".join(packages_json)

if __name__ == "__main__":
    import sys
    packages = None

    with open('package_list.txt', 'r') as f:
        packages = f.read().split()

    if packages is None:
        sys.stderr.write('No package defined in package_list.txt\n')
        sys.exit(1)

    with open('packages.json', 'w') as f:
        f.write(
"""\
{
    "schema_version": "1.2",
    "packages": [\
"""
        )
        f.write(build_packages_json_file(packages))
        f.write(
"""
    ]
}\
"""
        )
