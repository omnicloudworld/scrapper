# pylint: disable=W0401,W0614,C0114

from skyant.tools.duty.general import *  # noqa=F403
from skyant.tools.duty.venv import *  # noqa=F403
from skyant.tools.duty.pypi import *  # noqa=F403

from duty import duty

@duty
def inita(ctx, name: str = 'dev'):
    '''
    Initialize environment in .venv/{name}. Default name=dev. You can use `duty init name`
    Temporary for local usage

    Args:
        venv: Name of your virtual environment.
    '''

    ctx.run(f'python3.10 -m venv .venv/{name}', title='Make venv')
    ctx.run(f'. .venv/{name}/bin/activate && pip3 install --upgrade pip', title='Upgrade pip')
    ctx.run(f'. .venv/{name}/bin/activate && pip3 install --upgrade wheel pylint isort ipykernel', title='Base install')
    ctx.run(f'. .venv/{name}/bin/activate && pip3 install --upgrade -r .venv/{name}.req', title='Installing requirements')

