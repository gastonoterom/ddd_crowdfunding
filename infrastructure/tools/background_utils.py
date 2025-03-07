import asyncio
from asyncio import Task
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Coroutine


class BackgroundTaskService:
    """Low-level service for running background tasks in run fire forget mode"""

    def __init__(self) -> None:
        self.__tasks: set[Task] = set()
        self.__MAX_THREAD_POOL_SIZE = 100

        self.__background_thread_pool_executor = ThreadPoolExecutor(
            max_workers=self.__MAX_THREAD_POOL_SIZE,
            thread_name_prefix="background_worker_",
        )

    def run_fire_forget_coroutine(self, coroutine: Coroutine) -> None:
        """Schedules a task for an async coroutine, executed in the background"""
        task = asyncio.create_task(coroutine)

        self.__tasks.add(task)
        task.add_done_callback(self.__tasks.discard)

    def run_fire_forget_sync(self, func: Callable) -> None:
        """Wrap a sync callable in an async coroutine and run it in the background"""
        coroutine = self.run_async(func=func)

        self.run_fire_forget_coroutine(coroutine)

    async def run_async[T](self, func: Callable[..., T]) -> T:
        """
        Runs a callable on the background thread pool executor using the current thread's
          I/O loop instance.
        """

        return await asyncio.get_event_loop().run_in_executor(
            self.__background_thread_pool_executor, func
        )

    async def await_tasks(self) -> None:
        """Await all background tasks to complete"""
        tasks = list(self.__tasks)

        if not tasks:
            return

        await asyncio.wait(tasks)


background_service = BackgroundTaskService()
