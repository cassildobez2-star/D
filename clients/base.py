from abc import ABC, abstractmethod

class BaseClient(ABC):

    @abstractmethod
    async def search(self, query: str):
        pass

    @abstractmethod
    async def get_chapters(self, manga_id: str):
        pass

    @abstractmethod
    async def download(self, chapter_id: str, folder: str):
        pass
