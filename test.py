import re
import os
import shutil
import unittest
import time
from src.search import Search
from src.download import Download
from src.engine import Engine

class TestSearch(unittest.TestCase):
    def test_song_search(self):
        """
        Tests if search works correctly
        """
        query = "Reverse Sound Effect - Copyright free sound effects"
        result = Search(query).results
        s1, s2 = query.split(" ")[:2]
        self.assertTrue(re.search(rf'\b{s1}\b', result[0]["title"], re.IGNORECASE))
        self.assertTrue(re.search(rf'\b{s2}\b', result[0]["title"], re.IGNORECASE))
        self.assertEqual(len(result), 20)
        for res in result:
            self.assertTrue(bool(re.match(r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w\-]{11}", res["url"])))
        time.sleep(30)

class TestDownload(unittest.TestCase):
    def test_song_download(self):
        """
        Tests if search-download integration works correctly
        """
        query = "Reverse Sound Effect - Copyright free sound effects"
        result = Search(query).results[0]["url"]
        dl = Download(result)
        dir = dl.get_name()

        path = os.path.join("downloads", dir)
        self.assertTrue(os.path.isdir(path))

        audio_path = os.path.join(path, "audio.mp3")
        self.assertTrue(os.path.isfile(audio_path))

        meta_path = os.path.join(path, "metadata.json")
        self.assertTrue(os.path.isfile(meta_path))

        self.assertGreaterEqual(os.path.getsize(audio_path), 128)
        self.assertGreaterEqual(os.path.getsize(meta_path), 32)
        
class TestEngine(unittest.TestCase):
    def test_song_processing(self):
        """
        Tests if engine integration works correctly
        """
        e = Engine()
        dir = "b34263ce6e427d2f161f5bd52035682ae5a79bc1eeaa3616edcd7577d0870d5c"
        path = os.path.join("downloads", dir)
        e.enqueue(path)
        for _ in range(60):
            if e.is_done(path):
                break
            time.sleep(1)
        
        path = os.path.join(path, "htdemucs", "audio")
        self.assertTrue(os.path.isdir(path))

        vocals_path = os.path.join(path, "vocals.mp3")
        self.assertTrue(os.path.isfile(vocals_path))

        no_vocals_path = os.path.join(path, "no_vocals.mp3")
        self.assertTrue(os.path.isfile(no_vocals_path))
        
        self.assertGreaterEqual(os.path.getsize(vocals_path), 128)
        self.assertGreaterEqual(os.path.getsize(no_vocals_path), 128)
        

if __name__ == '__main__':
    unittest.main()
    shutil.rmtree(os.path.abspath("downloads"))