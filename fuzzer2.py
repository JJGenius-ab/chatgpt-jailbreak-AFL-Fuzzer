import asyncio

from fuzzer import parse_args, run


if __name__ == "__main__":
    print("fuzzer2.py is a legacy entrypoint. Running the safe fuzzer.py workflow.")
    asyncio.run(run(parse_args()))
