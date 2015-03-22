# -*- coding: utf-8 -*-

from fabric.api import (
    lcd,
    local,
    task)


@task
def clean():
    local('rm -rf wheelhouse')
    local('rm -rf dist')
    local('rm -rf build')

    with lcd('doc'):
        local('make clean')


@task
def docs():
    with lcd('doc'):
        local('make html')


@task
def push():
    local('git push origin')
    local('git push github')
    local('git push bitbucket')


@task
def push_tags():
    local('git push --tags origin')
    local('git push --tags github')
    local('git push --tags bitbucket')


@task
def pypi():
    local('python setup.py sdist bdist_wheel')
    local('twine upload dist/*')
