'''
'''

from os import environ as env
from pathlib import Path

import yaml
from setuptools import setup

with open('./setup.yml', 'r', encoding='utf-8') as vars_file:
    conf = yaml.safe_load(vars_file)

kwargs = {
    'name': f'{conf["NAMESPACE"].replace(".", "-")}',
    'version': f'{conf["VERSION"]}.{env.get("BUILD_SUFFIX", "")}{conf.get("MINOR", "0")}',
    'author': conf['AUTHOR'],
    'author_email': conf['EMAIL'],
    'description': conf['DESCR'],
    'url': conf['HOME'],
    'keywords': conf['KEYWORDS'],
    'packages': conf['MODULES'],
    'namespace_modules': [conf['NAMESPACE']],
    'python_requires': conf['PYTHON_REQ'],
    'classifiers': conf['CLASSIFIERS'],
    'install_requires': conf['REQUIREMENTS']
}

if 'LICENSE' in conf:
    kwargs['license'] = conf['LICENSE']

if Path('README.md').is_file():

    with open('README.md', 'r', encoding='utf-8') as md:
        long_description = md.read()

    if len(long_description) > 0:
        kwargs['long_description_content_type'] = 'text/markdown'
        kwargs['long_description'] = long_description


def add_urls(key: str, alias: str = None) -> None:
    '''
    Check env.yml & add value to project_urls.
    '''

    if 'project_urls' not in kwargs:
        kwargs['project_urls'] = {
            'Source & issues': env.get('CI_PROJECT_URL', 'http://localhost')
        }

    name = alias if alias else key.capitalize()
    if key in conf and conf[key] != '':
        kwargs['project_urls'][name] = conf[key]


add_urls('DOCUMENTATION', 'Documentation')

setup(**kwargs)
