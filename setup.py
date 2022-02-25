#!/usr/bin/env python

"""
Copyright (C) 2022 Red Hat, Inc. (https://github.com/Commonjava/charon)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from setuptools import setup, find_packages


setup(
    packages = [
        'charon',
        'charon.cmd',
        'charon.pkgs',
        'charon.utils',
        'charon.template',
    ],

    package_data = {
        'charon.template': [
            '*.j2',
        ],
    },

    install_requires = [
        'boto3',
        'click',
        'ruamel.yaml',
        'requests',
        'semantic_version',

        "enum34 ; python_version < '3.4'",
        "typing_extensions ; python_version < '3.8'",
    ],

    tests_require = [
        'boto3_type_annotations',
        'moto',
    ],

    entry_points = {
        "console_scripts": [
            "charon = charon:cli",
        ],
    },
)


# The end.
