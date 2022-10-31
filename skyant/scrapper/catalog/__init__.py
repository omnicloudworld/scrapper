'''
Package for getting a structured data from a catalog like website.

Catalog in current context is an any site that displayed teaser of information on the
search result page and full data on the item page.

An example of catalog is the search results or e-commerce website.

Package contains next objects:

- SearchPage - the handler of the page with search results
- ItemPage - the handler of the page with details about the item
- Router - provide a features for dynamical switch between different Search/ItemPage
    depending on URL
'''

from enum import Enum as _Enum

from ._item import ItemPage
from ._router import Router
from ._search import SearchPage


class Source(_Enum):
    '''
    Selector for identity how source should be processed
    '''

    PARENT = 'parent'
    CHILD = 'child'
