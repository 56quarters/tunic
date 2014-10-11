# -*- coding: utf-8 -*-

import tunic.api


def test_public_exports():
    exports = set([item for item in dir(tunic.api) if not item.startswith('_')])
    declared = set(tunic.api.__all__)

    assert exports == declared, 'Exports and __all__ members should match'

