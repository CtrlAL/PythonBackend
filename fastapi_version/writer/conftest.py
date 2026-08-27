import sys, types

if "asyncore" not in sys.modules:
    import asyncio
    asyncore = types.ModuleType("asyncore")

    class dispatcher:
        def __init__(self, *a, **k):
            pass

    asyncore.dispatcher = dispatcher

    def loop(*a, **k):
        pass

    asyncore.loop = loop
    sys.modules["asyncore"] = asyncore
