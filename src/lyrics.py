import os
import re
import time
from concurrent import futures

import lyricsgenius
import requests
import undetected_chromedriver as uc
from aeneas.executetask import ExecuteTask
from aeneas.task import Task
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langdetect import detect
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class Lyrics:
    """
    Gets lyrics for the song in available sources and saves them .srt file
    Takes path to directory
    """

    load_dotenv()
    __threads = 1
    __executor = futures.ThreadPoolExecutor(__threads)
    __GENIUS_API_TOKEN = os.getenv("GENIUS_API_TOKEN")
    __genius = lyricsgenius.Genius(
        __GENIUS_API_TOKEN,
        skip_non_songs=True,
        excluded_terms=["(Remix)", "(Live)"],
    )

    def __init__(self, artist: str, song_name: str, path: str):
        self.song_name = song_name
        self.artist = artist
        self.path = path
        self.success = True
        self.__lyricer = self.__executor.submit(self.__lyrics_wrapper)

    def is_done(self) -> bool:
        """
        Awaits for end of creating lyrics map and returns when it's done and
        if everything has gone right
        """
        self.__lyricer.result()
        return self.success

    def __lyrics_wrapper(self):
        try:
            lyrics = self.__get_song_lyrics()
            with open(
                os.path.join(self.path, "lyrics.txt"),
                "w",
                encoding="utf-8",
            ) as file:
                file.write(lyrics)
        except Exception as e:
            self.success = False
            return print(f"wrapper: {e!s}")

        try:
            print("Start processing using ananas...")
            language = detect(lyrics)
            config_string = f"task_language={language}|is_text_type=plain|os_task_file_format=srt"
            t = Task(config_string=config_string)
            t.audio_file_path_absolute = os.path.join(
                self.path, "htdemucs", "audio", "vocals.mp3"
            )
            t.text_file_path_absolute = os.path.join(
                self.path, "lyrics.txt"
            )

            ExecuteTask(t).execute()

            self.__write_srt(
                t.sync_map, os.path.join(self.path, "lyrics.srt")
            )
            try:
                os.remove(os.path.join(self.path, "lyrics.txt"))
            except Exception as e:
                print(f"remover: {e!s}")

        except Exception as e:
            self.success = False
            return print(f"ananas: {e!s}")

    def __write_srt(self, sync_map, output_path):
        """
        Converts sync map to .srt
        """

        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        with open(output_path, "w", encoding="utf-8") as f:
            for i, fragment in enumerate(sync_map.fragments):
                adjusted_start = float(fragment.begin)
                adjusted_end = float(fragment.end)
                if i > 0:
                    adjusted_start = max(0.0, adjusted_start - 0.5)
                    adjusted_end -= 0.5

                start = format_time(adjusted_start)
                end = format_time(adjusted_end)
                f.write(
                    f"{i + 1}\n{start} --> {end}\n{fragment.text.strip()}\n\n"
                )

    def __bing_search_tekstowo(self):
        """
        Searches Bing for Tekstowo lyrics using Selenium and undetected-chromedriver
        """
        query = f"site:tekstowo.pl {self.artist} {self.song_name}"
        search_url = "https://www.bing.com"

        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument(
            "--disable-blink-features=AutomationControlled"
        )
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36"
        )
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = uc.Chrome(options=options)

        try:
            driver.get(search_url)
            time.sleep(2)

            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(4)

            results = driver.find_elements(By.CSS_SELECTOR, "h2 > a")
            for result in results:
                href = result.get_attribute("href")
                if href and "tekstowo.pl/piosenka," in href:
                    return href

            print("found no hrefs")
            return None

        except Exception as e:
            print(f"Error during search: {e}")
            return None

        finally:
            driver.quit()

    def __get_tekstowo_lyrics(self):
        print("Searching tekstowo...")
        url = self.__bing_search_tekstowo()
        if url is None:
            return
        print("Got response from bing...")
        response = requests.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        lyrics_div = soup.find("div", {"class": "song-text"})
        print("Fetching lyrics from tekstowo div...")
        if not lyrics_div:
            return None

        for br in lyrics_div.find_all("br"):
            br.replace_with("\n")

        lyrics = lyrics_div.get_text(separator="\n").strip()
        lyrics = re.sub(r"\n{2,}", "\n", lyrics)
        return self.__clean_tekstowo_lyrics(lyrics)

    def __delete_useless_lines(self, line):
        if not line.startswith("Zwrotka") and not line.startswith(
            "Refren"
        ):
            return line

    def __clean_tekstowo_lyrics(self, raw_lyrics):
        lyrics = raw_lyrics.splitlines()
        lyrics = list(filter(self.__delete_useless_lines, lyrics))
        return "\n".join(lyrics[2:-2])

    def __get_genius_lyrics(self):
        """
        Searches genius for lyrics as a backup
        """
        try:
            print("Searching genius...")
            self.song_name = self.song_name.split("(")[0]
            song = self.__genius.search_song(
                self.song_name, self.artist
            )
            if song and song.lyrics:
                return self.__clean_genius_lyrics(song.lyrics)
        except Exception as e:
            print(f"Unable to find lyrics on Genius: {e}")
        return None

    def __clean_genius_lyrics(self, raw_lyrics):
        cleaned_lines = [
            line
            for line in raw_lyrics.splitlines()
            if not re.match(
                r"\[.*?(Verse|Chorus).*?\]", line, re.IGNORECASE
            )
        ]
        cleaned = "\n".join(cleaned_lines).strip()
        return cleaned

    def __get_song_lyrics(self):
        print("Searching for lyrics...")
        if os.path.exists(f"{self.path}/lyrics.srt"):
            return
        lyrics = self.__get_tekstowo_lyrics()
        if lyrics:
            print("Found lyrics on tekstowo")
            return lyrics

        lyrics = self.__get_genius_lyrics()
        if lyrics:
            print("Found lyrics on genius")
            return lyrics

        self.success = False
        print(f"Unable to find lyrics for: {self.artist} - {self.song_name}")
        raise Exception(
            f"Unable to find lyrics for: {self.artist} - {self.song_name}"
        )
