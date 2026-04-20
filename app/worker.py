import asyncio
import traceback

async def some_async_function():
    try:
        # Your asynchronous code here
        pass
    except Exception as e:
        # Improved error logging
        print(f"Exception occurred: {e}")
        print(traceback.format_exc())

async def main():
    await asyncio.wait_for(some_async_function(), timeout=5)

if __name__ == '__main__':
    asyncio.run(main())