import yt_dlp  # type: ignore
from hashlib import sha256
from concurrent import futures
from os import makedirs
from multiprocessing import cpu_count
import json


class Download:
    __threads = cpu_count() * 2 if cpu_count() <= 2 else cpu_count() + 1
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
        song_dir = f"downloads/{self.__name}"
        makedirs(song_dir, exist_ok=True)
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
            "quiet": True,
            "extractor-args": "youtube:player-skip=js",
        }

        with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:

            def helper():
                info = ytdl.extract_info(link, download=False)
                data = Download.parse_info(info, link)
                with open(metadata_file, "w") as output:
                    json.dump(data, output, indent=4)

            self.__downloader = self.__executor.submit(ytdl.download, [link])
            self.__informator = self.__executor.submit(helper)

    def is_ready(self) -> bool:
        """
        Tells if download is ready
        """
        return self.__downloader.done() and self.__informator.done()

    def get_name(self) -> str:
        """
        Awaits for end of downloading and returns directory name
        when it is finished
        """
        self.__informator.result()
        self.__downloader.result()
        if self.__name == "":
            raise Exception("Something gone wrong with your download")
        return self.__name
