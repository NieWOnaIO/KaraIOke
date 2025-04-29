import demucs

class Engine:
    def __init__(self, songPath: str):
        """
        Starts processing song given by local songPath
        """
        self.process_song()
        raise NotImplementedError()

    def is_ready(self) -> bool:
        """
        Whether song is ready to be sent do client
        """
        raise NotImplementedError()

    def process_song(self) -> int:
        """
        Processes song, returns status code
        """
        raise NotImplementedError()