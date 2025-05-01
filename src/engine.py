from typing import List
import demucs # type: ignore

class Engine:
    def __init__(self):
        """
        Holds a collection of tasks left to complete, 
        and processes them whenever possible.
        """
        self.task_queue: List[Engine.Task] = []
        self.currently_processing: Engine.Task | None = None
        raise NotImplementedError()

    def enqueue(self, path: str) -> bool:
        """
        Adds a song to queue via its path, starts processing if first in queue

        Args:
            path (str): Absolute path to a song directory

        Returns:
            bool: Was enqueueing successfull
        """
        raise NotImplementedError()
    
    def process_song(self) -> int:
        """
        Processes a single song inside queue, handles switching to next song in queue

        Returns:
            status_code (int): 0: OK, 1: Failed
        """
        raise NotImplementedError()
    
    def remove_expired(self) -> int:
        """
        Removes all expired songs from memory

        Returns:
            int: Number of expired songs removed
        """
        raise NotImplementedError()
    
    class Task:
        """
        Holds information about a single song being set to process

        Args:
            audio_path (str): Absoulte path to an audio file to process
        """
        def __init__(self, audio_path: str):
            self.is_done: bool = False
            self.has_failed: bool = False
            self.input_path: str = audio_path
            self.output_path: str | None = None
            self.expire_time: str | None = None
            raise NotImplementedError()