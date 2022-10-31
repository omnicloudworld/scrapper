# pylint: disable=missing-docstring

from __future__ import annotations

import logging as log
from abc import ABC
from typing import ClassVar
from enum import Enum

from lxml import html


class Field(ABC):
    '''
    The abstract class for defining a single entity of data that should be extracted from a web.

    Inherited classes will be extracted data from provided source.
    Defining a subclass you have to provide Xpath selectors which will be used to extract data.

    As a source for processing must be send single lxml.html.HtmlElement or dictionary of more them.
    If source will be a dictionary the class property "source" musty be defined.

    The Field class provides features for autocorrection extracted data. For example you can
    automatically replace "км/г" or "км/г" with km/h. For this feature you must only provide an
    autocorrection dictionary.

    Xpath selectors reverts an array, but the Field by default revert a single value from array. If
    you want to get a full array please set attribute array to True.

    Also the Field provides the solution for injection custom python code to prepare an
    extracted data. For this reason please define your own parser method.

    **Class Properties:**

    | Name | Type | Description | Default |
    | ---- | ---- | ----------- | ------- |
    | selectors | list of strings | Array of Xpath strings; all string will be joined using OR operator ||
    | source | enumerator of strings | Enumerator element which defines target key in source tree ||
    | autocorrection | dictionary from lists of strings | The dictionary for normalize string ||
    | array | bool | Flag for marks data as array | False |
    '''

    selectors: ClassVar[list[str]]
    source: ClassVar[Enum]
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
            assert isinstance(cls.source, Enum), \
                'The "source" argument must be a Enum!'

        if hasattr(cls, 'autocorrection'):
            assert isinstance(cls.autocorrection, dict), 'The autocorrection argument should be a dictionary!'

            for key, value in cls.autocorrection.items():
                assert isinstance(value, list), \
                    f'The "autocorrection" argument should contain list as values!\nPlease fix {key}!'
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
        Instance constructor

        Args:
            tree: lxml.html.HtmlElement or dict from them; dictionary requires the class attribute source

        Raises:
            ValueError: if tree is a dictionary but source is not defined in the class
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
        '''
        The stub of parser; current procedure return original data from self.parser; you can
        recreate this method if you want to use own logic
        '''
        return self.content

    def normalizer(self, origin: str) -> str:
        '''
        Processor for normalizing strings; the origin string will be replaced by the normalized value from
        the dictionary.

        ```json title="example of reffbook:"
        {
            "normalized value 1": [
                "1. variant 1",
                "1. variant 2"
            ],
            "normalized value 2": [
                "2. variant 1",
                "2. variant 2"
            ]
        }
        ```

        Args:
            origin: The string to normalize
            reffbook: A dictionary with the data for normalization strings

        Raises:
            ValueError: If reffbook contains invalid value of element

        Returns:
            The normalized string
        '''

        for key, value in self.autocorrection.items():

            if not isinstance(value, list):
                raise ValueError('Reffbook\'s value must be a list!')

            value.append(key)
            if origin in value:
                return key

        return origin

    def __call__(self):
        '''
        Runner for getting and normalizing the data
        '''

        try:
            data = self.parser()
            if hasattr(self, 'autocorrection'):
                if isinstance(data, str):
                    data = self.normalizer(data)
                elif isinstance(data, list):
                    data = [
                        self.normalizer(i) if isinstance(i, str) else i for i in data
                    ]

        except Exception as ex:  # pylint: disable=broad-except
            log.warning(f'Field {self.__class__.__name__} did\'t processed!\n{ex}')
            return None

        return data
