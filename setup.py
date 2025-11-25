# Copyright 2025 RDK Management
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages

def read_version():
    with open("VERSION", "r") as f:
        return f.read().strip()

setup(
    name='sc',
    version=read_version(),
    author="RDK Management",
    description="An entry-point for running SC plugins.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rdkcentral/sc",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'Click>=8',
        'pyyaml~=6.0',
        'rich>=14',
        'requests==2.31.0', # Docker SDK breaks on 2.32.0
        'docker~=7.0',
        'gitpython>=3',
        'pydantic>=2',
        'prompt_toolkit',
        'repo_library @ git+https://github.com/rdkcentral/sc-repo-library.git@master',
        'git_flow_library @ git+https://github.com/rdkcentral/sc-git-flow-library.git@master',
        'sc_manifest_parser @ git+https://github.com/rdkcentral/sc-manifest-parser.git@main'
    ],
    entry_points={
        'console_scripts': [
            'sc = sc.cli:entry_point',
        ]
    }
)