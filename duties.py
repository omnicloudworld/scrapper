# pylint: disable=missing-module-docstring


from os import (
    environ as env,
    path
)

from shutil import rmtree
from duty import duty
import yaml
import json


@duty
def bsd(ctx):
    '''
    Build & Serv the Documentation.
    '''

    ctx.run(
        'mkdocs build --config-file .mkdocs.yml --site-dir .html',
        title='Building documentation'
    )

    ctx.run(
        'mkdocs serve --config-file .mkdocs.yml --dev-addr 0.0.0.0:8008',
        title='Serving on http://localhost:8008/'
    )


@duty
def install(ctx):
    '''
    Install the current package.
    '''

    env['CI_PIPELINE_IID'] = '0'
    env['BUILD_SUFIX'] = 'dev'

    with open('./setup.yml', 'r', encoding='utf-8') as vars_file:
        conf = yaml.safe_load(vars_file)

    install_cmd = ''.join(
        [
            'pip3.10 install --force-reinstall --no-build-isolation --user ./dist/',
            f'{conf["NAMESPACE"].replace(".", "-")}-{conf["VERSION"]}.{env["BUILD_SUFIX"]}0.tar.gz; ',
        ]
    )

    try:
        ctx.run('python3 -m build --no-isolation .', title='Building')
        ctx.run(install_cmd, title='Installing')
    finally:
        rmtree(f'{conf["NAMESPACE"].replace(".", "_")}.egg-info', ignore_errors=True)
        rmtree(f'{path.join(env["PWD"], "dist")}', ignore_errors=True)


@duty
def gauth(ctx):
    '''
    Login to Google Cloud Platform.
    '''

    ctx.run(
        'gcloud beta auth login --update-adc --enable-gdrive-access --add-quota-project-to-adc --brief',
        title='Login'
    )

    project = env['GPROJECT'] if 'GPROJECT' in env else input('Please enter GCP project id: ')
    ctx.run(
        f'gcloud config set project {project}',
        title='Set project'
    )

@duty
def requirements(ctx):
    '''
    Install development requirements & package requirements
    '''

    with open('./setup.yml', 'r', encoding='utf-8') as vars_file:
        req = ' '.join(yaml.safe_load(vars_file)['REQUIREMENTS'])

    ctx.run('pip3 install --upgrade pip', title='Upgrading pip')
    ctx.run(f'pip3 install --upgrade {req}', title='Installing package requirements')
    ctx.run('pip3 freeze > .venv/dev.pip', title='Upgrading dev.pip')


@duty
def devinit(ctx):
    '''
    Initialize environment
    '''

    ctx.run('python3.10 -m venv .venv/dev', title='Make venv')
    ctx.run('. .venv/dev/bin/activate', title='Activate')
    requirements(ctx)


@duty
def devupgrade(ctx):
    '''
    Full upgrade current environment
    '''

    ctx.run('pip3 install --upgrade pip', title='Upgrading pip')
    ctx.run('pip3 install --upgrade -r .venv/dev.pip', title='Installing current requirements')

    out_json = ctx.run(
        'pip3 --disable-pip-version-check list --outdated --format=json',
        title='Getting outdated'
    )
    out_str = " ".join([x["name"] for x in json.loads(out_json)])

    if len(out_str.strip()) > 0:
        ctx.run(f'pip3 install --upgrade {out_str}', title='Upgrading all')
        ctx.run('pip3 freeze > .venv/dev.pip', title='Upgrading dev.pip file')
    else:
        print('You have actually packages.')
