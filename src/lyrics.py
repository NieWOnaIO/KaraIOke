from concurrent import futures
import os
import requests
from bs4 import BeautifulSoup
import re
import lyricsgenius
import re
from aeneas.executetask import ExecuteTask
from aeneas.task import Task
from langdetect import detect
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

class Lyrics:
    """
    Gets lyrics for the song in available sources and saves them .srt file
    Takes path to directory
    """
    load_dotenv()
    __threads = 1
    __executor = futures.ThreadPoolExecutor(__threads)
    __GENIUS_API_TOKEN = os.getenv("GENIUS_API_TOKEN")
    __genius = lyricsgenius.Genius(__GENIUS_API_TOKEN, skip_non_songs=True, excluded_terms=["(Remix)", "(Live)"])
    
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
            with open(os.path.join(self.path, "lyrics.txt"), "w", encoding="utf-8") as file:
                file.write(lyrics)
        except Exception as e:
            self.success = False
            return print(f"wrapper: {str(e)}")

        try:
            language = detect(lyrics)
            config_string = f"task_language={language}|is_text_type=plain|os_task_file_format=srt"
            t = Task(config_string=config_string)
            t.audio_file_path_absolute = os.path.join(self.path, "htdemucs", "audio", "vocals.mp3")
            t.text_file_path_absolute = os.path.join(self.path, "lyrics.txt")

            ExecuteTask(t).execute()

            self.__write_srt(t.sync_map, os.path.join(self.path, "lyrics.srt"))
            try:
                os.remove(os.path.join(self.path, "lyrics.txt"))
            except Exception as e:
                print(f"remover: {str(e)}")

        except Exception as e:
            self.success = False
            return print(f"ananas: {str(e)}")

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
                start = format_time(float(fragment.begin))
                end = format_time(float(fragment.end))
                f.write(f"{i+1}\n{start} --> {end}\n{fragment.text.strip()}\n\n")


    def __bing_search_tekstowo(self):
        """
        Searches Bing for Tekstowo lyrics using Selenium and undetected-chromedriver
        """
        query = f"site:tekstowo.pl {self.artist} {self.song_name}"
        search_url = "https://www.bing.com"

        options = uc.ChromeOptions()
        #options.add_argument("--headless")  # Usuń, jeśli chcesz widzieć okno przeglądarki
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = uc.Chrome(options=options)

        try:
            driver.get(search_url)
            time.sleep(2)

            # Wyszukiwanie
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(4)  # Czas na załadowanie wyników

            # Zbieranie wyników
            results = driver.find_elements(By.CSS_SELECTOR, "h2 > a")
            for result in results:
                href = result.get_attribute("href")
                if href and "tekstowo.pl/piosenka," in href:
                    return href

            print("found no hrefs")
            return None  # Jeśli nie znaleziono

        except Exception as e:
            print(f"Error during search: {e}")
            return None

        finally:
            driver.quit()

    def __get_tekstowo_lyrics(self):
        url = self.__bing_search_tekstowo()
        if url == None:
            return 
        
        response = requests.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        lyrics_div = soup.find("div", {"class": "song-text"})
        if not lyrics_div:
            return None

        for br in lyrics_div.find_all("br"):
            br.replace_with("\n")

        lyrics = lyrics_div.get_text(separator="\n").strip()
        lyrics = re.sub(r'\n{2,}', '\n', lyrics)
        return self.__clean_tekstowo_lyrics(lyrics)

    def __delete_useless_lines(self, line):
        if not line.startswith("Zwrotka") and not line.startswith("Refren"):
            return line
        
    def __clean_tekstowo_lyrics(self, raw_lyrics):
        lyrics = raw_lyrics.splitlines()
        lyrics = list(filter(self.__delete_useless_lines, lyrics))
        return '\n'.join(lyrics[2:-2])

    def __get_genius_lyrics(self):
        """
        Searches genius for lyrics as a backup
        """
        try:
            self.song_name = self.song_name.split("(")[0]
            song = self.__genius.search_song(self.song_name, self.artist)
            if song and song.lyrics:
                return self.__clean_genius_lyrics(song.lyrics)
        except Exception as e:
            print(f"Unable to find lyrics on Genius: {e}")
        return None

    def __clean_genius_lyrics(self, raw_lyrics):
        match = re.search(r"\[Verse.*?\]", raw_lyrics)
        if not match:
            return raw_lyrics.strip()

        start = match.start()
        end_marker = re.search(r"\[Music Video\]", raw_lyrics)
        end = end_marker.start() if end_marker else len(raw_lyrics)

        cleaned = raw_lyrics[start:end].strip()

        return cleaned

    def __get_song_lyrics(self):
        lyrics = self.__get_tekstowo_lyrics()
        if lyrics:
            return lyrics

        lyrics = self.__get_genius_lyrics()
        if lyrics:
            return lyrics

        self.success = False
        raise Exception(f"Unable to find lyrics for: {self.artist} - {self.song_name}")