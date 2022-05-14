import json
import random

from locust import HttpUser, task, between, TaskSet

"""По требованиям пиковая нагрузка - 500 одновременных пользователей: 80%-неавторизованные, 20% - авторизованные."""

"locust -f locustfile.py --host=http://127.0.0.1:8000 --csv=reports/report_locust --headless -u 500"


class SimpleUser(HttpUser):
    """Неавторизаванный пользователь."""
    weight = 4

    @task
    def v1_screenings_list(self):
        """Получаем все доступные Показы."""
        self.client.get("/api/v1/screenings")


class AuthUser(HttpUser):
    """Авторизаванный пользователь."""
    weight = 1

    def on_start(self):
        """Авторизация пользователя."""
        response = self.client.post("/api/token/", json={"username": "antenna", "password": "not98765"})
        self.auth_token = response.json().get("access")
        return super().on_start()

    @task
    def v1_seats_list(self):
        """Получаем все доступные Места."""
        self.client.get("/api/v1/seats/", headers={"Authorization": f"Bearer  {self.auth_token}"})

    @task
    def v1_seats_read(self):
        """Выполняем запрос для первого доступного Места."""
        response = self.client.get("/api/v1/seats/", headers={"Authorization": f"Bearer  {self.auth_token}"}).text
        seat_id = json.loads(response)["results"][0]["id"]
        self.client.get(f"/api/v1/seats/{seat_id}/", headers={"Authorization": f"Bearer  {self.auth_token}"})

    @task
    def v1_seats_create(self):
        """Создаем рандомное Место для первого доступного Показа."""
        rand_seat = random.randint(1, 150)
        response = self.client.get("/api/v1/screenings").text
        screening_id = json.loads(response)["results"][0]["screenings"][0]["id"]
        self.client.post("/api/v1/seats/", headers={"Authorization": f"Bearer  {self.auth_token}"},
                         json={"screening": screening_id, "seat_number": rand_seat})


class UserBehavior(TaskSet):
    wait_time = between(1, 2)
