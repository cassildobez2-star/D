import asyncio

class ChapterQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.worker_task = None

    async def start_worker(self, processor):
        if not self.worker_task:
            self.worker_task = asyncio.create_task(self.worker(processor))

    async def worker(self, processor):
        while True:
            chat_id, chapter = await self.queue.get()
            try:
                await processor(chat_id, chapter)
            except Exception as e:
                print("Erro no worker:", e)
            finally:
                self.queue.task_done()

    async def add(self, chat_id, chapter):
        await self.queue.put((chat_id, chapter))
