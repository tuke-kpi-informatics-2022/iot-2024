# main.py
import uasyncio as asyncio
from src.app import Application

async def main():

    # Instantiate your app
    app = Application()

    await app.run()  # Another async method that handles sensor updates

# The actual MicroPython entry point:
asyncio.run(main())
