from multiprocessing import Manager, Process
from typing import List
import time
import os
import shutil

class Engine:
    """
    Main engine class <br>
    Usage: <br>
        - Create engine: e = Engine() <br>
        - Run the engine: e.run() <br>
        - Enqueue songs on demand via e.enqueue()
    """
    def __init__(self):
        """
        Holds a collection of tasks left to complete, completed ones,
        and processes them whenever possible.
        """
        self.manager = Manager()
        self.task_queue: List[dict] = self.manager.list()
        self.processed_songs: List[dict] = self.manager.list()

    def enqueue(self, path: str) -> bool:
        """
        Adds a song to queue via its path, starts processing if first in queue

        Args:
            path (str): Absolute path to a song directory

        Returns:
            bool: Was enqueueing successfull
        """
        if not os.path.isdir(path):
            return False
        
        task = self.manager.dict({
            "is_done": False,
            "has_failed": False,
            "input_path": os.path.join(path, "audio.mp3"),
            "output_path": path,
            "expire_time": None
        })

        self.task_queue.append(task)
        return True


    
    def run(self):
        """
        Main Engine loop, handles switching tasks and processing them, processing doesn't block new enqueues
        """
        print("Engine started.")
        while True:
            if len(self.task_queue) == 0:
                time.sleep(1)
                continue

            task = self.task_queue.pop(0)
            print(f"Processing: {task['input_path']}")
            process = Process(target=Engine._process_wrapper, args=(task,))
            process.start()
            process.join()

            if task["is_done"]:
                self.processed_songs.append(task)
            
            self._cleanup_expired()


    
    @staticmethod
    def _process_wrapper(task: dict):
        """
        Processes a single song inside queue
        """
        try:
            import demucs.separate
            demucs.separate.main(["--mp3", "--two-stems", "vocals", "-o", task["output_path"], task["input_path"]])
            task["is_done"] = True
            task["has_failed"] = False
            task["expire_time"] = time.time() + 600
        except Exception:
            task["is_done"] = True
            task["has_failed"] = True
            task["expire_time"] = time.time() + 3600
    
    def _cleanup_expired(self) -> int:
        """
        Deletes songs that have expired to save space

        Returns:
            int: Number of deleted songs
        """
        now = time.time()
        to_del = []
        for song in self.processed_songs:
            if song["expire_time"] <= now:
                to_del.append(song["output_path"])
        for path in to_del:
            try:
                shutil.rmtree(path)
                print("Removed " + path + " from memory")
            except Exception as e:
                print("There was an error removing " + path + " error: " + e)
        return len(to_del)