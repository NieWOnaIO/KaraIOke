import os
import shutil
import time
from concurrent import futures
from typing import Union

import demucs.separate

from download import DOWNLOADS_PATH, Download


class Task:
    """
    Class representing a single task
    """

    __threads = 1
    __executor = futures.ThreadPoolExecutor(__threads)
    EXPIRATION_TIME = 600

    def __init__(self, item):
        if type(item) is str:
            self.__item = None
            self.__path = item
        else:
            self.__item = item
            self.__path = Task.get_path(item)
        self.__worker = Task.__executor.submit(self.__process_wrapper)
        # for this to not be undefined
        # proper expiration time will be counted since end of processing
        self.__expiration_time = -Task.EXPIRATION_TIME

    def __process_wrapper(self):
        """
        Processes a single song inside queue
        """
        if os.path.exists(
            os.path.join(self.__path, "htdemucs/audio/vocals.mp3")
        ):
            return
        if self.__item is not None:
            self.__item.wait_for()

        demucs.separate.main(
            [
                "--mp3",
                "--two-stems",
                "vocals",
                "-o",
                self.__path,
                os.path.join(self.__path, "audio.mp3"),
            ]
        )
        self.__expiration_time = time.time()

    def is_done(self) -> bool:
        """
        Tells if processing is done
        """
        return self.__worker.done()

    def wait_for(self):
        """
        Awaits for end of task
        """
        self.__worker.result()

    def cleanup(self) -> bool:
        """
        Deletes directories and songs when they expire
        """
        if not self.is_done():
            return False
        if self.__expiration_time <= time.time():
            print(self.__path)
            try:
                shutil.rmtree(self.__path)
                return True
            except:
                return False
        return False

    @staticmethod
    def get_path(item: Union[str, Download]) -> str:
        """
        Returns path that will be key in tasks queue
        """
        if type(item) is str:
            # just in case
            if not os.path.isdir(item):
                item = f"{DOWNLOADS_PATH}/{item}"
            if not os.path.isdir(item):
                raise Exception("Path expected")
            return item
        elif type(item) is Download:
            return Download.get_download_dir(item.get_name())
        raise Exception("Path or download task expected")


class Engine:
    """
    Main engine class <br>
    Usage: <br>
        - Create engine: e = Engine() <br>
        - Enqueue songs on demand via e.enqueue()
    """

    def __init__(self, clean_on_startup: bool = True):
        """
        Holds a collection of tasks left to complete, completed ones,
        and processes them whenever possible.
        """
        self.__tasks: dict[str, Task] = {}

        if clean_on_startup:
            shutil.rmtree(DOWNLOADS_PATH, True)

    def enqueue(self, item: Union[str, Download]):
        """
        Adds a song to queue via its path, starts processing if first in queue

        Args:
            path (str|Download): Absolute path to a song directory or
            task that is beeing downloaded to execute after it finishes

        Returns:
            bool: Was enqueueing successfull
        """
        path = Task.get_path(item)
        if path in self.__tasks:
            return

        self.__tasks[path] = Task(item)
        self.__cleanup_expired()

    def is_done(self, path: str) -> bool:
        """
        Tells if song is ready to be downloaded
        """
        return path in self.__tasks and self.__tasks[path].is_done()

    def wait_for(self, path: str):
        """
        Awaits for end of processing
        """
        self.__tasks[path].wait_for()

    def __cleanup_expired(self) -> int:
        """
        Deletes songs that have expired to save space

        Returns:
            int: Number of deleted songs
        """
        to_delete = []
        for path, task in self.__tasks.items():
            if task.cleanup():
                to_delete.append(path)

        for path in to_delete:
            self.__tasks.pop(path)

        return len(to_delete)
