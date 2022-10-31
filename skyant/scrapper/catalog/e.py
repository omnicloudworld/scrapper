'''
Exceptions of skyant.parser.catalog
'''


class WrongBase64(Exception):
    '''
    If string can't be decoded as base64!

    Args:
        additional: The additional information for identity page from
    '''

    def __init__(self, additional: str | None = None, **kw):

        self.additional = additional
        self.message = 'Provided string can\'t be decoded as base64!'
        if additional:
            self.message += f'\n{additional}'

        super().__init__(self.message, **kw)
