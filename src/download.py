import json
import os
from concurrent import futures
from hashlib import sha256
from multiprocessing import cpu_count

import yt_dlp  # type: ignore

DOWNLOADS_PATH = "downloads"


def do_nothing():
    pass


class Download:
    __threads = cpu_count() if cpu_count() >= 2 else cpu_count() + 1
    __executor = futures.ThreadPoolExecutor(__threads)

    @staticmethod
    def parse_info(info: dict, link: str) -> dict:
        return {
            "link": link,
            "title": info.get("track") or info.get("title"),
            "author": info.get("artist") or info.get("uploader"),
            "album": info.get("album") or "Unknown",
            "release": info.get("release_year")
            or info.get("upload_date")[:4],
            "duration": info.get("duration"),
        }

    def __init__(self, link: str):
        """
        Starts downloading video given by link and stores
        name of folder with results internally
        """
        self.link = link
        self.__name = sha256(link.encode()).hexdigest()
        song_dir = f"{DOWNLOADS_PATH}/{self.__name}"

        if os.path.exists(song_dir):
            self.__worker = self.__executor.submit(do_nothing)
            return

        os.makedirs(song_dir)
        song_file = f"{song_dir}/audio.%(ext)s"
        metadata_file = f"{song_dir}/metadata.json"

        ytdl_opts = {
            "format": "bestaudio/best",
            "extract-audio": True,
            "outtmpl": song_file,
            "no-post-overwrites": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "112k",
                }
            ],
            "quiet": False,
        }

        def helper():
            with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
                info = ytdl.extract_info(link, download=False)
                with open("info", "w") as output:
                    json.dump(info, output, indent=4)
                data = Download.parse_info(info, link)
                with open(metadata_file, "w") as output:
                    json.dump(data, output, indent=4)
                ytdl.download([link])

        self.__worker = self.__executor.submit(helper)

    def is_ready(self) -> bool:
        """
        Tells if download is ready
        """
        return self.__worker.done()

    def wait_for(self):
        """
        Awaits for end of downloading
        """
        self.__worker.result()

    def get_name(self) -> str:
        """
        Returns name of directory with audio or raises exception
        if something gone wrong
        """
        if self.__name == "":
            raise Exception("Something gone wrong with your download")
        return self.__name

    @staticmethod
    def get_download_dir(str) -> str:
        """
        Returns download directory name for engine
        """
        return f"{DOWNLOADS_PATH}/{str}"
