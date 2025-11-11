import time

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_time=30):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.opened_at = None

    def allow_request(self):
        if self.opened_at:
            if time.time() - self.opened_at > self.recovery_time:
                # half-open: allow a request
                return True
            return False
        return True

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = time.time()
            print("Circuit opened")

    def record_success(self):
        self.failures = 0
        self.opened_at = None
