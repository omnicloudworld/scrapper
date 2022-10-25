'''
'''

import re
from abc import ABC
from types import ModuleType
from typing import ClassVar

from .._loader import Loader
from validators import url as url_validator

from ._item import ItemPage
from ._search import SearchPage


class Router(ABC):

    variants: ClassVar[
        list[tuple[re.Pattern, ModuleType]]
    ]

    def __init_subclass__(cls, **kw):

        for pattern, mod in cls.variants:

            assert isinstance(pattern, re.Pattern), \
                f'The first argument should be a regex compiled expression!\nWas be received {print(pattern)} of type {type(pattern)} instead!'  # pylint: disable=line-too-long
            assert isinstance(mod, ModuleType), \
                f'The second argument should be a module!\nWas be received {mod.__name__} of type {type(mod)} insted!'  # pylint: disable=line-too-long

            assert hasattr(mod, 'CatalogLoader'), \
                f'The module {mod.__name__} hasn\'t atribute CalogLoader!'
            assert issubclass(mod.CatalogLoader, Loader), \
                f'The attribute CatalogLoader should be a skyant.parser.Loader subclass!\nWas received different in {mod.__name__}!'  # pylint: disable=line-too-long

            assert hasattr(mod, 'ItemLoader'), \
                f'The module {mod.__name__} hasn\'t atribute ItemLoader!'
            assert issubclass(mod.ItemLoader, Loader), \
                f'The attribute ItemLoader should be a skyant.parser.Loader subclass!\nWas received different in {mod.__name__}!'  # pylint: disable=line-too-long

            assert hasattr(mod, 'CatalogPage'), \
                f'The module {mod.__name__} hasn\'t atribute CatalogPage!'
            assert issubclass(mod.CatalogPage, SearchPage), \
                f'The attribute CatalogPage should be a skyant.parser.catalog.SearchPage subclass!\nWas received different in {mod.__name__}!'  # pylint: disable=line-too-long

            assert hasattr(mod, 'ItemPage'), \
                f'The module {mod.__name__} hasn\'t atribute ItemPage!'
            assert issubclass(mod.ItemPage, ItemPage), \
                f'The attribute ItemPage should be a skyant.parser.catalog.ItemPage subclass!\nWas received different in {mod.__name__}!'  # pylint: disable=line-too-long

        return super().__init_subclass__(**kw)

    def __init__(self, url: str, **kw):

        assert url_validator(url), 'The argument "url" shuld be a valid URL!'
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
            raise RuntimeError('')

        super().__init__(**kw)

    @property
    def CatalogLoader(self) -> Loader:
        '''
        '''

        return self._CatalogLoader

    @property
    def CatalogPage(self) -> SearchPage:
        '''
        '''

        return self._CatalogPage

    @property
    def ItemLoader(self) -> Loader:
        '''
        '''

        return self._ItemLoader

    @property
    def ItemPage(self) -> ItemPage:
        '''
        '''

        return self._ItemPage

    def get_catalog(self) -> SearchPage:
        '''
        '''

        return self.CatalogPage(self.url)
