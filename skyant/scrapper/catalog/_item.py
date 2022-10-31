# pylint: disable=missing-docstring

import logging as log
from abc import ABC
from base64 import b64decode as b64d
from copy import deepcopy
from inspect import isclass
from typing import ClassVar

from lxml import html
from pydantic import BaseModel

from . import e
from .. import Field, Loader


class ItemPage(ABC):
    '''
    This objects loads the item page & orchestrate fields processing

    **Class Properties:**

    | Name | Type | Description |
    | ---- | ---- | ----------- |
    | Child | skyant.parser.Field | Field that defines the URL to item page |
    | Loader | skyant.parser.Loader | Loader for the item page |
    | datamap | dict | Dictionary as a template for making the parsed data |
    | Adept | pydantic.BaseModel | BaseModel or inherited object for validating data |
    '''

    Child: ClassVar[Field]
    Loader: ClassVar[Loader]
    datamap: ClassVar[dict]
    Adept: ClassVar[BaseModel | None]

    def __init_subclass__(cls, **kw):

        assert issubclass(cls.Child, Field), \
            'The attribute "Child" must be a string!'

        assert issubclass(cls.Loader, Loader), \
            'The attribute "Loader" must be a SeleniumLoader or SimpleLoader instance!'

        assert isinstance(cls.datamap, dict), \
            'The attribute "datamap" must be a dictionary!'
        ItemPage._datamap_validator(cls.datamap)

        if hasattr(cls, 'Adept'):
            assert issubclass(cls.Adept, BaseModel), \
                'The attribute "Adept" must be a BaseModel instance!'
        else:
            cls.Adept = None

        return super().__init_subclass__(**kw)

    def __init__(
        self,
        parent: str | html.HtmlElement,
        datamap: dict = None,
        **kw
    ):
        '''
        Args:
            parent: The source of item card from the search page
            datamap: A dictionary of Fields

        Raises:
            WrongBase64: If source contains a string that is not a valid base64
        '''

        self._data = datamap if datamap else deepcopy(self.datamap)
        self.driver = Loader.driver

        if isinstance(parent, str):
            try:
                parent = html.fromstring(b64d(parent).decode())
            except Exception as ex:
                raise e.WrongBase64(self.__class__.__name__) from ex

        assert isinstance(parent, html.HtmlElement), \
            'Argument "parent" must be lxml.html.HtmlElement or it dump as base64!'

        self.tree = {'parent': parent}

        self.url = self.Child(tree=parent)()
        assert self.url, 'Empty url is not allowed!'

        self.tree['child'] = self.Loader(self.url)()
        self._data = self._processing(self._data)

        try:
            self._adept = self.Adept(**self._data) if self.Adept else None
        except Exception as ex:  # pylint: disable=broad-except
            self._bad_data = True
            log.warning(f'Was got bad data from {self.url}!\n{self._data}\n{ex}')

        super().__init__(**kw)

    @staticmethod
    def _datamap_validator(data):
        '''
        The validator of datamap dictionary

        Args:
            data: datamap dictionary
        '''

        for key, field in data.items():

            if isclass(field) and issubclass(field, Field):
                assert hasattr(field, 'source'), \
                    f'The class in field {key} of datamap must has an attribute "source"!'

            if isinstance(field, dict):
                ItemPage._datamap_validator(field)

    def _processing(self, data):
        '''
        The handler for processing the item page base on the datamap

        Args:
            data: The datamap or them part

        Returns:
            Scrapped data
        '''

        for key, field in data.items():

            if isclass(field) and issubclass(field, Field):

                try:
                    data[key] = field(self.tree[field.source.value])()
                except Exception as ex:  # pylint: disable=broad-except
                    data[key] = None
                    log.warning(f'The page {self.url} wasn\'t parsed! Error message:\n{ex}')

            elif isinstance(field, dict):
                data[key] = self._processing(field)

            else:
                data[key] = field

        return data

    @property
    def model(self) -> BaseModel:
        '''
        Returns:
            A pydantic.BaseModel used to validate the data
        '''
        return self._adept

    def __call__(self) -> dict:
        if hasattr(self, '_bad_data') and self._bad_data:
            return None
        return self.model.json() if self.model else self._data
