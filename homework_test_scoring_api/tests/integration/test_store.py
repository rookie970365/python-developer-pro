# pylint: disable=C0114,C0115,C0116,C0301,W0621
from fakeredis import FakeServer, FakeRedis
from pytest import fixture, raises

from store import Store, RedisDBStorage


@fixture
def setup():
    store = Store(RedisDBStorage())
    store.storage.connect()
    server = FakeServer()
    store.storage.server = FakeRedis(server=server)
    store.set('hello', 'world')
    store.set('spam', 'eggs')
    return store, server


def test_get(setup):
    store, server = setup
    server.connected = True
    assert store.get('hello') == 'world'
    assert store.get('spam') == 'eggs'
    assert store.get('scramble') is None
    store.cache_set('spam', 'nothing')
    assert store.get('spam') == 'nothing'


def test_delete(setup):
    store, server = setup
    server.connected = True
    assert store.get('hello') == 'world'
    store.delete('hello')
    assert store.get('hello') is None


def test_cache_get(setup):
    store, _ = setup
    assert store.cache_get('spam') == 'eggs'
    assert store.cache_get('hello') == 'world'


def test_connection_failed(setup):
    store, server = setup
    server.connected = False
    with raises(ConnectionError):
        store.get('hello')
    with raises(ConnectionError):
        store.set('foo', 'bar')


def test_connection_ok(setup):
    store, server = setup
    server.connected = True
    assert store.get('spam') == 'eggs'
