import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()

logger = logging.getLogger(__name__)

class Hashmap:


    def __init__(self, size: int = 1000, default_ttl: int = 60) -> None:
        self.size = size
        self.default_ttl = default_ttl

        self.hash_map = [[] for _ in range(self.size)]


    def hash_function(self, key) -> int:
        sum_of_chars = 0

        if key is None:
            raise ValueError("Key must be passed")

        if isinstance(key, str):
            for char in key:
                sum_of_chars += ord(char)
        elif isinstance(key, int):
            sum_of_chars += int(key)

        return sum_of_chars % self.size


    def expire(self, ttl: int | None = None):
        active_ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + active_ttl

        return expires_at


    def put(self, key, value, ttl: int | None = None):
        if value is None or key is None:
            raise TypeError("One or more argument is missing")

        index = self.hash_function(key)
        bucket = self.hash_map[index]

        expires_at = self.expire(ttl)

        try:
            for i, item in enumerate(bucket):
                if item[0] == key:
                    bucket[i] = (key, value, expires_at)
                    logger.info(f"Value {value} updated in bucket {index}")
                    return
            bucket.append((key, value, expires_at))
            logger.info(f"Value {value} added to bucket {index}")
        except (TypeError) as e:
            logger.error(f"Error while updating or adding a value check the hashmap {e}")


    def get(self, key):
        if key is None:
            raise TypeError("One or more argument is missing")
        index = self.hash_function(key)
        bucket = self.hash_map[index]
        current_time = time.time()

        try:
            for item in bucket:
                if item[0] == key:
                    expires_at = item[2]

                    if expires_at is not None and current_time < expires_at:
                        return item[1]

                    self.remove(key)
                    return None

        except (TypeError) as e:
            logger.error(f"Error while retrieving value for the key {e}")

        logger.info(f"No value found for the key provided")
        return None


    def remove(self, key):
        index = self.hash_function(key)
        bucket = self.hash_map[index]

        try:
            for i, item in enumerate(bucket):
                if item[0] == key:
                    del bucket[i]
                    logger.info(f"Value {item[1]} removed from bucket {index}")
                    return
        except (ValueError) as e:
            logger.error(f"Error while deleting value for the key {e}")


    def _sweep(self):
            current_time = time.time()

            for bucket in self.hash_map:
                keys_to_delete = []
                for item in bucket:
                    if current_time > item[2]:
                        keys_to_delete.append(item[0])

                for key in keys_to_delete:
                    self.remove(key)


    async def check_and_delete_expired_keys(self):
        loop = asyncio.get_event_loop()

        while True:
            await loop.run_in_executor(executor, self._sweep)
            await asyncio.sleep(60)
