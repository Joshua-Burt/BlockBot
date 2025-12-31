import asyncio
import contextlib
import signal
import json

from log import log, log_error
from bot import create_bot

async def main_async():
    create_bot()
    
    # Import initialize now that the bot has been created
    import initialize
    config = initialize.get_config()

    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    
    def handle_signal():
        stop.set()
    
    loop.add_signal_handler(signal.SIGTERM, handle_signal)
    loop.add_signal_handler(signal.SIGINT, handle_signal)
    
    # Start bot
    task = asyncio.create_task(bot.start(config["token"]))
    
    # Wait for SIGTERM / SIGINT
    await stop.wait()
    
    # Cancel the bot.start task
    await log("Attempting to close connections...")
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
    
    # Ensure HTTP session cleanup
    await bot.close()
    await log("Connections closed successfully.")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_async())
    finally:
        loop.close()

if __name__ == "__main__":
    main()
