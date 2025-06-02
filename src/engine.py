from concurrent import futures
import time
import os
import shutil
import demucs.separate

class Task:
    """
    Class representing a single task
    """
    __threads = 1
    __executor = futures.ThreadPoolExecutor(__threads)

    def __init__(self, path):
        self.__expire_time = time.time() + 600
        self.__path = path
        self.__done = False
        self.__worker = Task.__executor.submit(self.__process_wrapper)

    def __process_wrapper(self):
        """
        Processes a single song inside queue
        """
        vocals_path = os.path.join(self.__path, "htdemucs/audio/vocals.mp3")
        if os.path.exists(vocals_path):
            self.__done = True
            return

        demucs.separate.main(["--mp3", "--two-stems", "vocals", "-o", self.__path, os.path.join(self.__path, "audio.mp3")])
        self.__done = True

    def is_done(self) -> bool:
        return self.__done
    
    def cleanup(self, now) -> bool:
        """
        Deletes directories and songs when they expire
        """
        if self.__expire_time <= now:
            try:
                shutil.rmtree(self.__path)
                return True
            except:
                return False
        return False


class Engine:
    """
    Main engine class <br>
    Usage: <br>
        - Create engine: e = Engine() <br>
        - Enqueue songs on demand via e.enqueue()
    """
    def __init__(self):
        """
        Holds a collection of tasks left to complete, completed ones,
        and processes them whenever possible.
        """
        self.__tasks: dict[str, Task] = {}
        path = "downloads"
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                self.__tasks[full_path] = Task(full_path)

    def enqueue(self, path: str):
        """
        Adds a song to queue via its path, starts processing if first in queue

        Args:
            path (str): Absolute path to a song directory

        Returns:
            bool: Was enqueueing successfull
        """
        if not os.path.isdir(path):
            raise Exception("Path expected")

        if path in self.__tasks:
            return

        self.__cleanup_expired()
        self.__tasks[path] = Task(path)


    def is_done(self, path) -> bool:
        """
        Tells if song is ready to be downloaded
        """
        return self.__tasks[path].is_done()


    def __cleanup_expired(self) -> int:
        """
        Deletes songs that have expired to save space

        Returns:
            int: Number of deleted songs
        """
        now = time.time()
        to_delete = []
        for path, task in self.__tasks.items():
            if task.cleanup(now):
                to_delete.append(path)

        for path in to_delete:
            self.__tasks.pop(path)

        return len(to_delete)
