#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import six

from .core import Iterable
from .function import Function
from .. import serializers, errors


class Functions(Iterable):

    marker = serializers.XMLNodeField('Marker')
    max_items = serializers.XMLNodeField('MaxItems')
    functions = serializers.XMLNodesReferencesField(Function, 'Function')

    def _name(self):
        return 'registration/functions'

    def _get(self, name):
        return Function(client=self._client, parent=self, name=name)

    def __contains__(self, item):
        if isinstance(item, six.string_types):
            function = self._get(item)
        elif isinstance(item, Function):
            function = item
        else:
            return False

        try:
            function.reload()
            return True
        except errors.NoSuchObject:
            return False

    def __iter__(self):
        return self.iterate()

    def iterate(self):
        params = {'expectmarker': 'true'}

        def _it():
            last_marker = params.get('marker')
            if 'marker' in params and \
                (last_marker is None or len(last_marker) == 0):
                return

            url = self.resource()
            resp = self._client.get(url, params=params)

            f = Functions.parse(self._client, resp, obj=self)
            params['marker'] = f.marker

            return f.functions

        while True:
            functions = _it()
            if not functions:
                break
            for function in functions:
                yield function

    def create(self, obj=None, **kwargs):
        function = obj or Function(parent=self, client=self._client, **kwargs)
        if function.parent is None:
            function._parent = self
        if function._client is None:
            function._client = self._client

        headers = {'Content-Type': 'application/xml'}
        data = function.serialize()

        self._client.post(self.resource(), data, headers=headers)

        function.reload()
        return function

    def delete(self, name):
        if not isinstance(name, Function):
            function = Function(name=name, parent=self)
        else:
            function = name
            name =name.name
        del self[name]  # release cache

        url = function.resource()

        self._client.delete(url)
