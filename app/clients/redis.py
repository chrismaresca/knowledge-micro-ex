# Typing imports
from typing import Callable, Dict, Type


# Redis imports
import redis
import redis.exceptions

import logging
import asyncio
from pydantic import BaseModel


class RedisClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RedisClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    # TODO: Update the host and port to read from .env
    def __init__(self, host: str = 'redis', port: int = 6379, db: int = 0):
        """
        Initialize the Redis client with connection parameters.
        """
        if not hasattr(self, 'initialized'):
            # Ensure initialization only happens once
            self.redis = redis.Redis(host=host, port=port, db=db)
            self.streams = {}
            # set the initialized flag to True
            self.initialized = True

    def create_consumer_group(self, event_name: str, group_name: str) -> None:
        """
        Create a consumer group for a given Redis stream.
        """
        try:
            # Create a group with the event name as the key and a group name
            self.redis.xgroup_create(name=event_name, groupname=group_name, mkstream=True)
            logging.info(f"Created consumer group '{group_name}' for event '{event_name}'")
        except redis.exceptions.ResponseError as e:
            logging.info(f"Consumer group '{group_name}' already exists or other error: {e}")

    def register_event(self, event_name: str, group_name: str) -> None:
        """
        Register an event with a consumer group.
        """

        # Add an event to the streams of this client
        self.streams[event_name] = group_name

        # Create the consumer group
        self.create_consumer_group(event_name=event_name, group_name=group_name)

    def produce_event(self, event_name: str, event_payload: BaseModel) -> None:
        """
        Produce an event to a specified Redis stream. This takes in an event payload which is a BaseModel via Pydantic.
        """
        try:
            # Event Payload transformed into a dictionary
            event_payload_dict = event_payload.model_dump()
            # Encode it as UTF-8 if its a string. TODO: Add support for flattening nested base models.
            encoded_event_payload = {k: v.encode('utf-8') if isinstance(v, str) else v for k, v in event_payload_dict.items()}
            self.redis.xadd(name=event_name, fields=encoded_event_payload)
            logging.info(f"Added the following event payload: {encoded_event_payload} to event '{event_name}'")
        except Exception as e:
            logging.error(f"Error producing message: {e}")

    async def consume_events(self, event_name: str, group_name: str, consumer_name: str, callback: Callable[[Dict], None]) -> None:
        """Consume events from a specified Redis stream and process them with a callback."""
        while True:
            try:
                # Process events
                events = self.redis.xreadgroup(groupname=group_name, consumername=consumer_name, streams={event_name: '>'}, count=1)
                if events:
                    for _, event_payload in events:
                        for event_id, event in event_payload:

                            # Log that consumption occured
                            logging.info(f"Consumed event ID {event_id}: {event}")

                            # handle the event
                            callback(event)

                            # Acknowledge event processing
                            self.redis.xack(event_name, group_name, event_id)
            except Exception as e:
                logging.error(e)
            await asyncio.sleep(1)  # Sleep for a short period to avoid tight loop

    def start_consumer(self, event_name: str, group_name: str, consumer_name: str, callback: Callable[[Dict], None]) -> None:
        """Start the consumer to process events using an asynchronous event loop."""
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.consume_events(event_name, group_name, consumer_name, callback))
        loop.run_until_complete(task)
