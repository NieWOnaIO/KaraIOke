import yt_dlp  # type: ignore
import hashlib


class Download:
    def __init__(self, link: str):
        """
        Starts downloading video given by link and stores
        name of folder with results internally
        """
        self.link = link
        self.__name = None  # place future here
        raise NotImplementedError()

    def is_ready(self) -> bool:
        """
        Returns readiness of download
        """
        # TODO some future status
        raise NotImplementedError()

    def get_name(self) -> str:
        """
        Awaits for end of downloading and returns directory name
        when it is finished
        """
        # TODO await for future here
        raise NotImplementedError()
