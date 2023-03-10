from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from types import FunctionType as function
import time

class EventHandler(LoggingEventHandler):

    def __init__(
        self,
        on_modified: function,
        logger = None
    ):
        self.on_modified = on_modified
        super().__init__(logger)

    def on_modified(self, event):
        if event.event_type == "modified":
            if event.is_directory:
                return
            print(f"Announcing that we need to rebuild the asgard route.\nModification at {event.src_path}")
            self.on_modified()


class Nelka(Observer):
    "An observer class for the cog source"

    def __init__(
        self,
        event_handler: LoggingEventHandler = None,
        track_only: list[str] = [], 
        timeout=3
    ):
        super().__init__(timeout)
        for path in track_only:
            self.schedule(event_handler, path, recursive=True)

    
class A:
    def __init__(self) -> None:
        self.a = "a"
    def test(self, event):
        print(self.a, event)


if __name__ == "__main__":
    a = A()
    observer = Nelka(EventHandler(on_modified=a.test), track_only=["."])
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()