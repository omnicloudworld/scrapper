# pylint: disable=missing-docstring

import logging as log
import time
from abc import ABC
from enum import Enum, unique
from os import environ as env
from typing import ClassVar

from lxml import html
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


@unique
class Method(Enum):
    '''
    '''

    MOUSE = 'mouse'
    ENTER = 'enter'
    SPACE = 'space'

    def __str__(self):
        return self.value

    def __call__(self):
        return self.value


class Loader(ABC):
    '''
    '''

    options: ClassVar[Options]
    timeout: ClassVar[int] = 3
    denotificators: ClassVar[list[tuple[Method, str]]]
    thereare: ClassVar[list[str]]
    click: ClassVar[list[tuple[Method, int, str]]]

    width: str = '1920'
    height: str = '1080'
    chromepath: str = '/usr/bin/google-chrome-stable'

    def __init_subclass__(cls, **kw):

        if not (hasattr(cls, 'options') and isinstance(cls.options, Options)):

            cls.options = Options()
            cls.options.add_argument('start-maximized')
            cls.options.binary_location = env.get('CHROME_PATH', str(cls.chromepath))
            cls.options.add_argument(
                f'--window-size={env.get("WINDOW_WIDTH", str(cls.width))},{env.get("WINDOW_HEIGHT", str(cls.height))}'  # pylint: disable=line-too-long
            )
            cls.options.add_argument('--headless')
            cls.options.add_argument('--disable-default-apps')
            cls.options.add_argument('--disable-dev-shm-usage')
            cls.options.add_argument('--no-sandbox')
            cls.options.add_argument('--enable-features="AllowAllCookies"')

        assert isinstance(cls.timeout, int) or cls.timeout <= 0, \
            f'Value of attribute "timeout" should be integer but provided {type(cls.timeout)}: {cls.timeout}!'

        return super().__init_subclass__(**kw)

    def _denotificators_(self, driver: WebDriver):
        '''
        '''

        free_timeout = self.timeout
        for method, element in self.denotificators:

            start = time.time()

            try:

                if method == Method.MOUSE:
                    WebDriverWait(driver, free_timeout).until(
                        EC.element_to_be_clickable(('xpath', element))
                    ).click()

                elif method == Method.ENTER:
                    WebDriverWait(driver, free_timeout).until(
                        EC.element_to_be_clickable(('xpath', element))
                    ).send_keys(Keys.ENTER)

                elif method == Method.SPACE:
                    WebDriverWait(driver, free_timeout).until(
                        EC.element_to_be_clickable(('xpath', element))
                    ).send_keys(Keys.SPACE)

                log.info(f'Done {method} on {element} from the page {self._url}!')

            except Exception as ex:  # pylint: disable=broad-except
                log.info(
                    f'Click on denotificator {element} from the page {self._url} return error!\n{ex}'  # pylint: disable=line-too-long
                )

            free_timeout -= round(time.time() - start)
            if free_timeout < 0:
                log.warning(f'Timeout on the element {element} from the page {self._url}!')

    def _thereare_(self, driver: WebDriver):
        '''
        '''

        free_timeout = self.timeout
        for element in self.thereare:

            start = time.time()
            WebDriverWait(driver, free_timeout).until(EC.presence_of_element_located(('xpath', element)))

            free_timeout -= round(time.time() - start)
            if free_timeout < 0:
                raise TimeoutError(f'Timeout on the element {element} from the page {self._url}!')

    def _click_(self, driver: WebDriver):
        '''
        '''

        free_timeout = self.timeout
        for method, count, element in self.click:

            counter = count
            start = time.time()
            confirmed_pages = 0

            while count == 0 or counter > 0:

                try:

                    if method == Method.MOUSE:
                        WebDriverWait(driver, free_timeout).until(
                            EC.element_to_be_clickable(('xpath', element))
                        ).click()

                    elif method == Method.ENTER:
                        WebDriverWait(driver, free_timeout).until(
                            EC.element_to_be_clickable(('xpath', element))
                        ).send_keys(Keys.ENTER)

                    elif method == Method.SPACE:
                        WebDriverWait(driver, free_timeout).until(
                            EC.element_to_be_clickable(('xpath', element))
                        ).send_keys(Keys.SPACE)

                    log.info(f'Done {method} on {element} from the page {self._url}!')
                    confirmed_pages += 1

                except Exception as ex:  # pylint: disable=broad-except

                    if confirmed_pages == 0:
                        log.info(ex)
                        log.warning(
                            f'Click on {element} from the page {self._url} was be stoped with exception!'
                        )
                    elif confirmed_pages > 0 and confirmed_pages < count:
                        log.info(
                            f'Click on {element} from the page {self._url} was be done {confirmed_pages} times from {count}!\n{ex}'  # pylint: disable=line-too-long
                        )
                    break

                counter -= 1

            free_timeout -= round(time.time() - start)
            if free_timeout < 0:
                log.warning(f'Timeout on the element {element} from the page {self._url}!')

    def __init__(
        self,
        url: str,
        **kw
    ):

        self._url = url

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.options
        )

        driver.get(url)

        if hasattr(self, 'denotificators'):
            try:
                self._denotificators_(driver)
            except TimeoutException as ex:  # pylint: disable=unused-variable
                log.warning(f'Timed out waiting "denotificators" for page {url} to load!')

        if hasattr(self, 'thereare'):
            try:
                self._thereare_(driver)
            except TimeoutException as ex:  # pylint: disable=unused-variable
                log.warning(f'Timed out waiting "thereare" for page {url} to load!')

        if hasattr(self, 'click'):
            try:
                self._click_(driver)
            except TimeoutException as ex:  # pylint: disable=unused-variable
                log.warning(f'Timed out waiting "click" for page {url} to load!')

        self._driver = driver

        super().__init__(**kw)

    @property
    def driver(self) -> webdriver.Chrome:
        return self._driver

    @property
    def html(self) -> str:
        return self.driver.page_source

    def __call__(self):
        return html.fromstring(self.html)

    def quit(self):
        self.driver.quit()
