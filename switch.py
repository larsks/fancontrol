try:
    import uasyncio as asyncio
except ImportError:
    import asyncio  # type: ignore[no-redef]

try:
    import requests
except ImportError:
    import urequests as requests  # type: ignore[no-redef]

import simplelog


class Switch:
    def __init__(self, addr):
        self._url = "http://{addr}/cm".format(addr=addr)
        self._lock = asyncio.Lock()
        self._log = simplelog.make_logger("switch@{}".format(addr))

    async def request(self, cmnd):
        async with self._lock:
            while True:
                try:
                    self._log("sending command: {}".format(cmnd), level=0)
                    requests.get(
                        "{url}?cmnd={cmnd}".format(
                            url=self._url, cmnd=cmnd.replace(" ", "%20")
                        )
                    )
                except OSError:
                    self._log("failed to communicate with switch (retrying)", level=3)
                    await asyncio.sleep(5)
                else:
                    self._log("command sent successfully", level=0)
                    break

    async def turn_on(self):
        self._log("turn on")
        await self.request("Power On")

    async def turn_off(self):
        self._log("turn off")
        await self.request("Power Off")

    async def is_on(self):
        res = await self.request("Power Status")
        data = res.json()
        self._log("current status = {}".format(data["POWER"]))
        return data["power"] == "ON"
