import enum

class SearchType(enum.Enum):
    TEXT = 0
    BEGINNING = 2
    ANY = 3

class ChangeType(enum.Enum):
    OVERWRITE = 0
    ADD_BEFORE_LINE = 1
    ADD_NEXT_LINE = 2

class Change:
    change_type: ChangeType
    change_query: str | None
    change_file_path: str | None
    limit: int | None
    def __init__(
            self,
            change_type: ChangeType,
            change_query: str | None = None,
            change_file_path: str | None = None,
            limit: int | None = 1
    ):
        self.change_type = change_type
        self.change_query = change_query
        self.change_file_path = change_file_path
        self.limit = limit
    def __str__(self) -> str:
        return f'CHANGE: "{self.change_type}":"{self.change_query or self.change_file_path}"({self.limit});'

class Search:
    file_path: str
    search_type: SearchType
    search_query: str | None
    def __init__(
            self,
            file_path:str,
            search_type: SearchType,
            search_query: str | None = None
    ) -> None:
        self.file_path = file_path
        self.search_type = search_type
        self.search_query = search_query

    def __str__(self) -> str:
        return f'SEARCH: "{self.file_path}":"{self.search_query}"({self.search_type});'


class Injection:
    change: Change
    search: Search

    def __init__(
            self,
            search: Search,
            change: Change,
    ) -> None:
        self.search = search
        self.change = change

    def __str__(self) -> str:
        return f'INJECTION:\n\t"{repr(str(self.search))}"\n\t"{repr(str(self.change))}";'