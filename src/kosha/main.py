import logging
from pydantic import BaseModel, Field
import uuid

logger = logging.getLogger(__name__)

class Hashmap:
    # I need a hash function which will basically take an input and give me the index value
    # Get function which will return me the value in that index
    # Initially let's say my array is of size 10
    # mod of 10 to get index between 0 - 9 and also have to handle chaining to make room for more values if they have the same index
    def __init__(self, size: int = 1000) -> None:
        self.size = size

        self.hash_map = [[] for _ in range(self.size)]

    def hash_function(self, key) -> int:
        if key is None:
            raise ValueError("Key must be passed")

        return sum(int(char) for char in key if char.isdigit()) % self.size

    def ttl(self, key):
        # Set a time for the key to live I can simply define this and extend my put function with this
        pass

    def put(self, key, value):
        if value is None or key is None:
            raise TypeError("One or more argument is missing")

        index = self.hash_function(key)
        bucket = self.hash_map[index]

        try:
            for i, (k,v) in enumerate(bucket):
                if k == key:
                    bucket[i] = (key, value)
                    logger.info(f"Value {value} updated in bucket {index}")
                    return
            bucket.append((key, value))
            logger.info(f"Value {value} added to bucket {index}")
        except (TypeError) as e:
            logger.error(f"Error while updating or adding a value check the hashmap {e}")

    def get(self, key):
        if key is None:
            raise TypeError("One or more argument is missing")
        index = self.hash_function(key)
        bucket = self.hash_map[index]

        try:
            for k,v in bucket:
                if k == key:
                    return v
        except (TypeError) as e:
            logger.error(f"Error while retrieving value for the key {e}")

        logger.info(f"No value found for the key provided")
        return None

    def remove(self, key):
        index = self.hash_function(key)
        bucket = self.hash_map[index]

        try:
            for i, (k, v) in enumerate(bucket):
                if k == key:
                    del bucket[i]
                    logger.info(f"Value {v} removed from bucket {index}")
                    return
        except (ValueError) as e:
            logger.error(f"Error while deleting value for the key {e}")


class KeyValueStore(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    hashmap: Hashmap | None = Field(default=None)
    ttl: int = Field(default=86400)
