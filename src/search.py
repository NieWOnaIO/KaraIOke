from typing import List

class Search:
    def __init__(self, query: str):
        """
        Holds information about a search done on a given query
        """
        self.query: str = query
        self.results: List[object] = []
        raise NotImplementedError()
    
    def search_query(self) -> bool:
        """
        Queries and saves results

        Returns:
            bool: Was query successfull
        """
        raise NotImplementedError()
    
    def serialize(self) -> str:
        """
        Serializes results to JSON ready to be returned by API

        Returns:
            str: JSON string of results
        """
        raise NotImplementedError()