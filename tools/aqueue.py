import asyncio

class AQueue(asyncio.Queue):
    async def put(self, item, user_id=0):
        await super().put((item, user_id))

    def qsize(self):
        return super().qsize()
