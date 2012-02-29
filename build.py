#!/usr/bin/env python
import os
import platform
import subprocess
import json
from string import Template


# ==== CONFIG ====
g_packages = ["SublimeAStyleFormatter", "SublimeAlternate"]


# Read every package.json file
def get_package_files(packages):
    system = platform.system()
    if system == "Windows":
        st2_packages_dir = os.path.join(os.environ["APPDATA"], "Sublime Text 2\\Packages")
    elif system == "Darwin":
        st2_packages_dir = "~/Library/Application Support/Sublime Text 2/Packages"
    else:
        st2_packages_dir = "~/.Sublime Text 2/Packages"
    package_files = []
    for package in packages:
        package_files.append(os.path.join(st2_packages_dir, package, "package.json"))
    return package_files


def shell_execute(args, working_dir):
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=working_dir)


def get_package_git_information(package_file):
    package_dir = os.path.dirname(package_file)
    # Get version
    proc_git_tag = shell_execute(['git', 'tag'], package_dir)
    latest_tags = proc_git_tag.communicate()[0].strip()
    latest_tags = latest_tags.split('\n')
    # Get the newest
    latest_tag = latest_tags[-1]
    latest_version = latest_tag[1:]
    # Get date
    proc_git_log = shell_execute(
        ['git', 'log', "--pretty=format:%ci", "-1", latest_tag], package_dir)
    last_modified = proc_git_log.communicate()[0].strip()
    last_modified = last_modified[:19]
    if (latest_tag == "" or latest_version == ""):
        raise Exception("No Git Version Information")
    return latest_tag, latest_version, last_modified


def get_package_json_information(package_file):
    # Parsing package.json, get params
    f = open(package_file, "r")
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
                        "version": "$latest_version",
                        "url": "https://nodeload.github.com/timonwong/$repo/zipball/$latest_tag"
                    }
                ]""")
    latest_tag, latest_version, last_modified = package_git_information
    json_platforms = []
    for platform in platforms:
        json_platforms.append(template_platform.substitute(platform=platform, latest_version=latest_version, \
                                                           latest_tag=latest_tag, repo=repo))
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
            "platforms": {$platforms
            }
        }""")

    packages_json = []
    for package_file in package_files:
        try:
            package_json_info = get_package_json_information(package_file)
            package_git_info = get_package_git_information(package_file)
            _, _, last_modified = package_git_info
            platforms = build_platforms_json_string(package_git_info, \
                                                    package_json_info["platforms"], \
                                                    package_json_info["repo"])
            packages_json.append(template_main.substitute(name=package_json_info["name"], \
                                                          description=package_json_info["description"], \
                                                          author=package_json_info["author"], \
                                                          homepage=package_json_info["homepage"], \
                                                          last_modified=last_modified, \
                                                          platforms=platforms))
        except:
            pass
    return ",".join(packages_json)

if __name__ == "__main__":
    f = open('packages.json', 'w')
    f.write("""{
    "schema_version": "1.2",
    "packages": [""")
    f.write(build_packages_json_file(g_packages))
    f.write("""
    ]
}""")
    f.close()
