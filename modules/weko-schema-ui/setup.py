# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of weko-schema-ui."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.2.2',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
]

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
    'xmlschema>=0.9.30',
]

install_requires = [
    'Flask-BabelEx>=0.9.2',
    'xmlschema>=0.9.30',
    'bibtexparser>=1.0.1',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('weko_schema_ui', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='weko-schema-ui',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='weko schema ui',
    license='GPLv2',
    author='National Institute of Informatics',
    author_email='wekosoftware@nii.ac.jp',
    url='https://github.com/wekosoftware/weko-schema-ui',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'weko_schema_ui = weko_schema_ui:WekoSchemaUI',
        ],
        'invenio_admin.views': [
            'weko_schema_ui_oai_schema = '
            'weko_schema_ui.admin:oai_schema_adminview',
        ],
        'invenio_base.api_apps': [
            'weko_schema_rest = weko_schema_ui:WekoSchemaREST',
        ],
        'invenio_i18n.translations': [
            'messages = weko_schema_ui',
        ],
        'invenio_assets.bundles': [
            'weko_schema_ui_js = weko_schema_ui.bundles:js',
        ],
        'invenio_search.mappings': [
            'weko = weko_schema_ui.mappings',
        ],
        'invenio_access.actions': [
            'schema_access = '
            'weko_schema_ui.permissions:action_schema_access',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 1 - Planning',
    ],
)
