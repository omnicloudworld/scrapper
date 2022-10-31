# pylint: disable=missing-docstring

import concurrent.futures
import logging as log
from abc import ABC
from base64 import b64encode as b64e
from typing import ClassVar

from lxml import html
from .. import Field, Loader

from ._item import ItemPage


class SearchPage(ABC):
    '''
    Object for processing the page with a search result & orchestration processing of entity pages.

    This class loads the web page by the skyant.parser.Loader that gets the search results using
    Items field.

    Class can click on the page link or on link "continue..."

    **Class Properties:**

    | Name | Type | Description |
    | ---- | ---- | ----------- |
    | Loader | skyant.parser.Loader | Class of Loader that loads the page |
    | Items | skyant.parser.Field | Class of Field that define search results (catalog) item |
    | Next | skyant.parser.Field | Class of Field that define next button on pager |
    | timeout | float OR int | Time out for waiting for page to load |
    '''

    Loader: ClassVar[Loader]
    Items: ClassVar[Field]
    Next: ClassVar[Field | None]
    timeout: ClassVar[int | float] = 3

    def __init_subclass__(cls, **kw):

        assert issubclass(cls.Loader, Loader), \
            'The "Loader" attribute must be a subclass of SeleniumLoader or SimpleLoader!'

        assert issubclass(cls.Items, Field), \
            'The "Items" attribute must be a subclass of Field!'

        assert isinstance(cls.timeout, (int, float)) and cls.timeout > 0, \
            'The "timeout" attribute must be a positive integer or float!'

        if hasattr(cls, 'Next'):
            assert issubclass(cls.Next, Field), \
                'The "Next" attribute must be a subclass of Field!'

        return super().__init_subclass__(**kw)

    def __init__(
        self,
        url: str,
        depth: int = 1,
        **kw
    ):
        '''
        Args:
            url: search page URL for processing
            depth: the number of times the next/more button should be pressed
        '''

        assert depth >= 0 and isinstance(depth, int), 'The depth must be int more that 0!'

        if not hasattr(self, 'Next') or self.Next is None:
            assert depth == 1, \
                'The class attribute "Next" is obligatory for the depth != 1!'

        self._depth = depth
        self._fields: list = []
        self._counter: int = 0
        self.driver = Loader.driver

        self._load(url)

        super().__init__(**kw)

    def _load(self, url) -> None:
        '''
        The handler for loading page content as manu as define in attribute depth

        Args:
            url: the url of first page
        '''

        while self._counter < self._depth or self._depth == 0:

            tree = self.Loader(url)()
            next_url = self.Next(tree)() if hasattr(self, 'Next') else None

            self._fields.extend(self.Items(tree)())

            self._counter += 1
            if next_url:
                return self._load(next_url)
            else:
                break

    def __call__(self, base64: bool = False) -> list[html.HtmlElement] | list[str]:
        '''
        _summary_

        Args:
            base64: The flag for converting data to a base64 string which will be send to REST API.

        Returns:
            List of loaded data
        '''
        return [b64e(html.tostring(i)).decode() for i in self._fields] if base64 else self._fields

    def mine(
        self,
        item: ItemPage,
        workers: int = 4
    ) -> list[dict]:
        '''
        _summary_

        Args:
            item: The class inherited from skyant.parser.catalog.ItemPage which orchestrate Fields
            workers: How many threads will be used for upload all found items

        Returns:
            Parsed & structured data
        '''

        data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []

            for card in self():

                try:
                    futures.append(executor.submit(item(card)))
                except Exception as ex:  # pylint: disable=broad-except
                    log.warning(f'Error during processing of item!\n{ex}')

            for future in concurrent.futures.as_completed(futures):

                try:
                    data.append(future.result())
                except Exception as ex:  # pylint: disable=broad-except
                    log.warning(f'Error during processing of item!\n{ex}')

        return data

    def items(self, item: ItemPage) -> list[ItemPage]:
        '''
        The handler for getting all items

        Args:
            item: The class inherited from skyant.parser.catalog.ItemPage which orchestrate Fields

        Returns:
            Uploaded items source as a list of objects
        '''

        return [item(i) for i in self()]
