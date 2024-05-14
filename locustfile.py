from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def load_test(self):
        self.client.get("/")

    # @task
    # def create_post(self):
    #     headers = {'content-type': 'application/json'}
    #     data = {"wr_ids": ['1'], "sw": "move"}
    #     self.client.post("/board/move/free", json=data, headers=headers)