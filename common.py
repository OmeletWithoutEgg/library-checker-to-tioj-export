import re
import requests
from os import getenv

import colorlog
from logging import basicConfig, getLogger

from bs4 import BeautifulSoup

logger = getLogger(__name__)


def prepare_colorlog():
    handler = colorlog.StreamHandler()
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'white',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        })
    handler.setFormatter(formatter)
    basicConfig(
        level=getenv('LOG_LEVEL', 'INFO'),
        handlers=[handler]
    )


class InputProxy():
    def __init__(self, inputs):
        self.inputs = inputs

    def find(self, regex):
        return [i for i in self.inputs
                if re.match(regex, i.attrs['name'])]


class UserTIOJ():
    def __init__(self, config):
        self.session = requests.Session()
        self.tioj_url = config.tioj_url
        self.login(config.username, config.password)

    def login(self, TIOJusername, TIOJpassword):
        logger.info('TIOJ logging in...')
        inputs = self.get_inputs('/users/sign_in')
        auth_token = inputs.find('authenticity_token')[0].attrs['value']
        rel = self.post('/users/sign_in', data={
            'authenticity_token': auth_token,
            'user[username]': TIOJusername,
            'user[password]': TIOJpassword,
            'user[remember_me]': '1',
            'commit': 'Sign in'
        })
        assert rel.status_code == 200
        logger.info('TIOJ login success')

    def get_inputs(self, endpoint):
        rel = self.get(endpoint)
        soup = BeautifulSoup(rel.text, 'html.parser')
        inputs = soup.find('form').find_all('input')
        return InputProxy(inputs)

    def get(self, endpoint, *args, **kwargs):
        return self.session.get(self.tioj_url + endpoint, *args, **kwargs)

    def post(self, endpoint, *args, **kwargs):
        return self.session.post(self.tioj_url + endpoint, *args, **kwargs)

    def patch(self, endpoint, *args, **kwargs):
        return self.session.patch(self.tioj_url + endpoint, *args, **kwargs)

    # def delete(self, endpoint, *args, **kwargs):
    #     return self.session.delete(self.tioj_url + endpoint, *args, **kwargs)

    # def put(self, endpoint, *args, **kwargs):
    #     return self.session.put(self.tioj_url + endpoint, *args, **kwargs)
