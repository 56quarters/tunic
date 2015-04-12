# -*- coding: utf-8 -*-

import tunic.core

from hypothesis import assume, given


@given(str)
def test_split_by_line_fuzz(text):
    lines = tunic.core.split_by_line(text)
    assert isinstance(lines, list)


@given(str)
def test_split_by_line_non_blank_fuzz(text):
    assume(text.strip())
    lines = tunic.core.split_by_line(text)
    assert len(lines) > 0


@given(str)
def test_get_current_path_fuzz(base):
    assume(base)
    current = tunic.core.get_current_path(base)
    assert current.endswith('/current')


@given(str)
def test_get_releases_path_fuzz(base):
    assume(base)
    current = tunic.core.get_releases_path(base)
    assert current.endswith('/releases')


@given(str)
def test_get_release_id_with_version_fuzz(version):
    assume(version is not None)
    release_id = tunic.core.get_release_id(version)
    assert release_id.endswith('-' + version)