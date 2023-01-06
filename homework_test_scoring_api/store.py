# pylint: disable=C0114,C0115,C0116,C0301
import functools
import json
import logging
import time

import redis

DELAY = 0.5


def reconnect(num_attempts):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for num in range(num_attempts):
                try:
                    return func(*args, **kwargs)
                except (TimeoutError, ConnectionError) as err:
                    logging.info("Cannot connect to Redis at %s attempt: %s ...", num, err)
                    time.sleep(DELAY)
            raise ConnectionError(f"Connection failed after {num_attempts} attempts")

        return wrapper

    return decorator


class RedisDBStorage:

    def __init__(self, host="localhost", port=6379, timeout=3):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.server = None

    def connect(self):
        self.server = redis.Redis(
            host=self.host,
            port=self.port,
            db=0,
            socket_connect_timeout=self.timeout,
            socket_timeout=self.timeout,
            decode_responses=True
        )

    def set(self, key, value, expires=None):
        try:
            return self.server.set(key, value, ex=expires)
        except redis.exceptions.TimeoutError:
            logging.error(TimeoutError)
        except redis.exceptions.ConnectionError as err:
            raise ConnectionError from err
        return None

    def get(self, key):
        try:
            value = self.server.get(key)
            if value is not None:
                try:
                    return json.loads(value)
                except json.decoder.JSONDecodeError:
                    return value.decode()
        except redis.exceptions.TimeoutError:
            logging.error(TimeoutError)
        except redis.exceptions.ConnectionError as err:
            raise ConnectionError from err
        return None

    def delete(self, key):
        try:
            self.server.delete(key)
        except redis.exceptions.TimeoutError:
            logging.error(TimeoutError)
        except redis.exceptions.ConnectionError as err:
            raise ConnectionError from err


class Store:
    ATTEMPTS = 5

    def __init__(self, storage):
        self.storage = storage

    def cache_get(self, key):
        return self.storage.get(key)

    def cache_set(self, key, value, expires=None):
        self.storage.set(key, value, expires)

    @reconnect(ATTEMPTS)
    def set(self, key, value):
        return self.storage.set(key, value)

    @reconnect(ATTEMPTS)
    def get(self, key, use_cache_if_error=True):
        if use_cache_if_error:
            try:
                return self.storage.get(key)
            except redis.exceptions.ConnectionError:
                logging.error(ConnectionError)
                return self.cache_get(key)
        else:
            return self.storage.get(key)

    @reconnect(ATTEMPTS)
    def delete(self, key):
        return self.storage.delete(key)
