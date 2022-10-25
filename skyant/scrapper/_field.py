# pylint: disable=missing-docstring

import logging as log
from abc import ABC
from enum import Enum as _Enum
from typing import ClassVar

from lxml import html


def normalizer(origin: str, reffbook: dict) -> str:
    '''
    '''

    for key, value in reffbook.items():

        if not isinstance(value, list):
            raise ValueError('Reffbook\'s value must be a list!')

        value.append(key)
        if origin in value:
            return key

    return origin


class SelectSource(_Enum):
    '''
    '''

    PARENT = 'parent'
    CHILD = 'child'


class Field(ABC):
    '''
    '''

    selectors: ClassVar[list[str]]
    source: ClassVar[SelectSource]
    autocorrection: ClassVar[dict]
    array: ClassVar[bool] = False

    def __init_subclass__(cls, **kw):

        if isinstance(cls.selectors, list):

            for selector in cls.selectors:
                assert isinstance(selector, str), 'The "selector" argument should be a list of string!'
        else:
            raise TypeError('The "selectors" argument should be a list of string!')

        cls._selector = ' | '.join(cls.selectors)

        if hasattr(cls, 'source'):
            assert isinstance(cls.source, SelectSource), \
                'The "source" argument must be a "SelectSource" property!'

        if hasattr(cls, 'autocorrection'):
            assert isinstance(cls.autocorrection, dict), 'The autocorrection argument should be a dictionary!'

            for key, value in cls.autocorrection.items():
                assert isinstance(value, list), \
                    f'The "autocorrection" argument should contain lista as values!\nPlease fix {key}!'
                for i in value:
                    assert isinstance(i, str), \
                        f'The "autocorrection" argument should contain a list of string!\nPlease fix {key}: {i}!'  # pylint: disable=line-too-long

        return super().__init_subclass__(**kw)

    def __init__(
        self,
        tree: html.HtmlElement | dict,
        **kw
    ):
        '''
        '''

        if isinstance(tree, dict):
            if not hasattr(self, 'source'):
                raise ValueError('The argument "tree" as dict requires an argument "source"')
            tree = tree[self.source.value]

        try:
            self.content = tree.xpath(self._selector)
        except Exception as ex:  # pylint: disable=broad-except
            log.warning(
                f'Could not processed the selector: {self.selectors} in {self.__class__.__name__}!\n{ex}'
            )
            self.content = None

        if self.content:
            if len(self.content) > 0:
                self.content = self.content if self.array else self.content[0]
            elif len(self.content) == 0:
                self.content = None

        if isinstance(self.content, str):
            self.content = self.content.strip()
        elif isinstance(self.content, list):
            self.content = [i.strip() if isinstance(i, str) else i for i in self.content]

        super().__init__(**kw)

    def parser(self):
        return self.content

    def __call__(self):

        try:
            data = self.parser()
            if hasattr(self, 'autocorrection'):
                if isinstance(data, str):
                    data = normalizer(data, self.autocorrection)
                elif isinstance(data, list):
                    data = [
                        normalizer(i, self.autocorrection) if isinstance(i, str) else i for i in data
                    ]

        except Exception as ex:  # pylint: disable=broad-except
            log.warning(f'Field {self.__class__.__name__} did\'t processed!\n{ex}')
            return None

        return data
