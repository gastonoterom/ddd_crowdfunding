import asyncio
import logging
from typing import Callable

from retry import retry

from infrastructure.events.messages import Command, Event, Message


logger = logging.getLogger(__name__)


class EventBus:
    def __init__(
        self,
    ) -> None:
        # Commands can have 1 and only 1 handler
        self._command_handlers: dict[type[Command], Callable] = {}

        # Events can have N handlers
        self._event_handlers: dict[type[Event], list[Callable]] = {}

    def register_command_handler(
        self, command: type[Command], handler: Callable
    ) -> None:
        self._command_handlers[command] = handler

    def register_event_handler(self, event: type[Event], handler: Callable) -> None:
        if event not in self._event_handlers:
            self._event_handlers[event] = []

        self._event_handlers[event].append(handler)

    @retry(
        tries=3,
        delay=0.1,
        jitter=0.1,
    )
    async def handle(self, message: Message) -> None:
        if isinstance(message, Command):
            await self._handle_command(message)

        elif isinstance(message, Event):
            await self._handle_event(message)

    async def _handle_command(self, command: Command) -> None:
        handler = self._command_handlers[type(command)]

        await handler(command)

    async def _handle_event(self, event: Event) -> None:
        handlers = self._event_handlers.get(type(event), [])

        result = await asyncio.gather(
            *[handler(event) for handler in handlers], return_exceptions=True
        )

        exceptions = [r for r in result if isinstance(r, Exception)]

        for exc in exceptions:
            logger.exception(f"Error handling event: {exc}")


event_bus = EventBus()
