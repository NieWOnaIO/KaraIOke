from typing import List
import yt_dlp
import json


class Search:
    def __init__(self, query: str):
        """
        Holds information about a search done on a given query
        """
        self.query: str = query
        self.results: List[dict] = []
        self.search_query()

    def search_query(self) -> bool:
        """
        Queries YouTube and saves top 20 results

        Returns:
            bool: Was query successfull
        """
        try:
            ydl_opts = {
                "quiet": True,
                "extract_flat": "in_playlist",
                "skip_download": True,
                "format": "bestaudio/best",
                "default_search": "ytsearch30",
                "noplaylist": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.query, download=False)

                if "entries" not in info:
                    return False
                self.results = []
                for entry in info["entries"]:
                    if not entry.get("id") or not entry.get("title"):
                        continue

                    self.results.append(
                        {
                            "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                            "title": entry.get("track")
                            or entry.get("title")
                            or "Unknown",
                        }
                    )

                    if len(self.results) >= 20:
                        break

                return bool(self.results)

        except Exception as e:
            print(f"Error during search: {e}")
            return False

    def serialize(self) -> str:
        """
        Serializes results to JSON ready to be returned by API

        Returns:
            str: JSON string of results
        """
        return json.dumps(self.results, indent=2)
