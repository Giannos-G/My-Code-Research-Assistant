#!/usr/bin/env python3
"""Entry point: python main.py"""

import asyncio

from assistant.agent import main

if __name__ == "__main__":
    asyncio.run(main())
