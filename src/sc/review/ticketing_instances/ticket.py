#!/usr/bin/env python3

class Ticket():

    def __init__(self, ticket_url: str, **kwargs):
        self._url = ticket_url
        self._contents = kwargs

    @property
    def author(self):
        return self._contents.get('author')

    @property
    def assignee(self):
        return self._contents.get('assignee')

    @property
    def comments(self):
        return self._contents.get('comments')

    @property
    def contents(self):
        return self._contents

    @property
    def id(self):
        return self._contents.get('id')

    @property
    def status(self):
        return self._contents.get('status')

    @property
    def target_version(self):
        return self._contents.get('target_version')

    @property
    def title(self) -> str:
        return self._contents.get('title')

    @property
    def url(self) -> str:
        return self._contents.get('url')

    def get(self, undeclared_property):
        return self._contents.get(undeclared_property)
