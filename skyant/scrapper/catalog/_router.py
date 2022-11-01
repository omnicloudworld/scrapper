'''
'''

import re
from abc import ABC
from types import ModuleType
from typing import ClassVar

from validators import url as url_validator

from .._loader import Loader
from ._item import ItemPage
from ._search import SearchPage


class Router(ABC):
    '''
    Select a module depending on a url; the module have to contains CatalogLoader, ItemLoader,
    ItemPage & CatalogPage objects.

    **Class Properties:**

    | Name | Type | Description |
    | ---- | ---- | ----------- |
    | variants | list of tuples | (re.pattern, module); if url matches to pattern then module will be used |
    '''

    variants: ClassVar[
        list[tuple[re.Pattern, ModuleType]]
    ]

    def __init_subclass__(cls, **kw):

        for pattern, mod in cls.variants:

            assert isinstance(pattern, re.Pattern), \
                f'The first argument should be a regex compiled expression!\nWas be received {print(pattern)} of type {type(pattern)} instead!'  # pylint: disable=line-too-long
            assert isinstance(mod, ModuleType), \
                f'The second argument should be a module!\nWas be received {mod.__name__} of type {type(mod)} instead!'  # pylint: disable=line-too-long

            assert hasattr(mod, 'CatalogLoader'), \
                f'The module {mod.__name__} hasn\'t attribute CatalogLoader!'
            assert issubclass(mod.CatalogLoader, Loader), \
                f'The attribute CatalogLoader should be a skyant.parser.Loader subclass!\nWas received different in {mod.__name__}!'  # pylint: disable=line-too-long

            assert hasattr(mod, 'ItemLoader'), \
                f'The module {mod.__name__} hasn\'t attribute ItemLoader!'
            assert issubclass(mod.ItemLoader, Loader), \
                f'The attribute ItemLoader should be a skyant.parser.Loader subclass!\nWas received different in {mod.__name__}!'  # pylint: disable=line-too-long

            assert hasattr(mod, 'CatalogPage'), \
                f'The module {mod.__name__} hasn\'t attribute CatalogPage!'
            assert issubclass(mod.CatalogPage, SearchPage), \
                f'The attribute CatalogPage should be a skyant.parser.catalog.SearchPage subclass!\nWas received different in {mod.__name__}!'  # pylint: disable=line-too-long

            assert hasattr(mod, 'ItemPage'), \
                f'The module {mod.__name__} hasn\'t attribute ItemPage!'
            assert issubclass(mod.ItemPage, ItemPage), \
                f'The attribute ItemPage should be a skyant.parser.catalog.ItemPage subclass!\nWas received different in {mod.__name__}!'  # pylint: disable=line-too-long

        return super().__init_subclass__(**kw)

    def __init__(self, url: str, **kw):
        '''
        Args:
            url: The url of web page

        Raises:
            RuntimeError: If url matches nothing patterns
        '''

        assert url_validator(url), 'The argument "url" should be a valid URL!'
        self.url = url

        found = False
        for pattern, mod in self.variants:

            if pattern.match(url):

                self._CatalogLoader = getattr(mod, 'CatalogLoader')  # pylint: disable=invalid-name
                self._CatalogPage = getattr(mod, 'CatalogPage')  # pylint: disable=invalid-name
                self._ItemLoader = getattr(mod, 'ItemLoader')  # pylint: disable=invalid-name
                self._ItemPage = getattr(mod, 'ItemPage')  # pylint: disable=invalid-name

                found = True
                break

        if not found:
            raise RuntimeError(f'Router hasn\'t module for url {url}')

        super().__init__(**kw)

    @property
    def CatalogLoader(self) -> Loader:  # pylint: disable=invalid-name
        '''
        Returns:
            The skyant.parser.Loader for loading the catalog page
        '''
        return self._CatalogLoader

    @property
    def CatalogPage(self) -> SearchPage:  # pylint: disable=invalid-name
        '''
        Returns:
            The skyant.parser.SearchPage for handling the catalog page
        '''
        return self._CatalogPage

    @property
    def ItemLoader(self) -> Loader:  # pylint: disable=invalid-name
        '''
        Returns:
            The skyant.parser.Loader for loading the item page
        '''
        return self._ItemLoader

    @property
    def ItemPage(self) -> ItemPage:  # pylint: disable=invalid-name
        '''
        Returns:
            The skyant.parser.ItemPage for handling the item page
        '''
        return self._ItemPage

    def get_catalog(self) -> SearchPage:
        '''
        Returns:
            The list of data from the catalog
        '''
        return self.CatalogPage(self.url)
