import threading
import time


class HeartbeatManager:
    def __init__(self, drm_client, interval=5):
        self.drm_client = drm_client
        self.interval = interval
        self.running = False
        self.thread = None
        self.on_failure_callback = None

    def start(self, on_failure):
        self.running = True
        self.on_failure_callback = on_failure
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _run(self):
        while self.running:
            result = self.drm_client.heartbeat()

            if not result.get("success"):
                if self.on_failure_callback:
                    self.on_failure_callback(result.get("error", "ERR_HEARTBEAT_LOST"))
                self.running = False
                break

            time.sleep(self.interval)