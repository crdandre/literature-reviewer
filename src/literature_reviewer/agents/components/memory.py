import sys
import time
import threading
from itertools import cycle
from datetime import datetime, timezone
from pydantic import BaseModel
from literature_reviewer.agents.components.agent_pydantic_models import ConversationHistoryEntry

class LoadingAnimation:
    def __init__(self):
        self.loading_event = threading.Event()
        self.loading_thread = None

    def start(self):
        def animate():
            for c in cycle(['|', '/', '-', '\\']):
                if self.loading_event.is_set():
                    break
                sys.stdout.write('\rProcessing ' + c)
                sys.stdout.flush()
                time.sleep(0.1)
            sys.stdout.write('\r' + ' ' * 20 + '\r')  # Clear the line

        self.loading_thread = threading.Thread(target=animate)
        self.loading_thread.start()

    def stop(self):
        self.loading_event.set()
        if self.loading_thread:
            self.loading_thread.join()

def run_with_loading(func):
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'loading_animation'):
            self.loading_animation = LoadingAnimation()
        if not self.loading_animation.loading_thread or not self.loading_animation.loading_thread.is_alive():
            self.loading_animation.start()
        try:
            return func(self, *args, **kwargs)
        finally:
            pass  # Don't stop the animation here
    return wrapper

def add_to_conversation_history(func):
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        heading = func.__name__
        timestamp = datetime.now(timezone.utc).isoformat()
        
        if isinstance(result, BaseModel):
            content_structure = result.__class__.__name__
            content = result.model_dump_json()
        else:
            content_structure = ""
            content = str(result)
        
        entry = ConversationHistoryEntry(
            agent_name=self.name,
            heading=heading,
            timestamp=timestamp,
            model=self.model_interface.model.model_name,
            content=content,
            content_structure=content_structure
        )
        self.conversation_history.entries.append(entry)
        
        if self.verbose:
            from .printout import print_latest_entry
            print_latest_entry(entry)
        
        return result
    return wrapper
