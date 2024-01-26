from locust import HttpUser, task, between, events
import logging

# Configure logging
logging.basicConfig(filename='locust_errors.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(message)s')

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def load_test(self):
        self.client.get("/")


@events.request.add_listener
def on_request(event, **kwargs):
    if not event.success:
        logging.error(f"Request failed: {event.request_type} {event.name}, Exception: {event.exception}")