import inspect
import random
from datetime import datetime, timedelta
from locust import HttpUser, task, between, TaskSet
from locust.user import wait_time

BASE_URL = "https://testapi.rizek.com/v1/api"

endpoints = {
    "new_signup": "/auth/signup",
    "send_otp": "/auth/sendOTP",
    "new_login": "/auth/login/phone",
    "user_exists": "/auth/isUserExists",
    "logout": "/client/auth/logout",
    'service_tree': "/cac/operating/services_tree?cityId=1",
    "create_new_job": "/client/jobs",
    "list_all_jobs": "/client/jobs/job"
}

headers = {'Content-Type': 'application/json'}
next11am = (datetime.now() + timedelta(days=1))
next11am = datetime(next11am.year, next11am.month,
                    next11am.day, 5).strftime("%Y-%m-%d%H:%S")


def get_url():
    """Gets the url that is base_url + endpoint for the caller

    Returns:
        str: URL correspoding to the endpoint name matching the caller method's name
    """
    # The calling method's name should be a key in the endpoints dict
    # If the name does not exist in the dict, the BASE URL is returned,
    # without an endpoint
    caller_name = inspect.stack()[1].function
    return BASE_URL + endpoints.get(caller_name, '')


class RizekAuthTaskSet(TaskSet):
    @task
    def user_exists(self):
        self.client.post(get_url(), headers=headers,
                         json={"phoneNumber": self.user.phone_number})

    @task(3)
    def service_tree(self):
        self.client.get(get_url(), headers=headers)

    @task(2)
    def create_new_job(self):
        self.client.post(get_url(), headers=self.user.headers,
                         json={"addressId": 1413,
                               "cityId": 1,
                               "description": "install TV",
                               "expectedDate": next11am,
                               "isPromoApplicable": True,
                               "media": [],
                               "paymentMethod": "cash",
                               "services": [
                                   {
                                       "heroes": 1,
                                       "hours": 1,
                                       "id": 35,
                                       "units": 0
                                   }
                               ],
                               "title": "Maintenance"
                               })

    @task(2)
    def list_all_jobs(self):
        resp = self.client.get(get_url(), headers=self.user.headers)
        print(self.user.phone_number, len(resp.json()['data']['upcoming']))


class RizekUser(HttpUser):
    def __init__(self, env) -> None:
        super().__init__(env)
        self.phone_number = '+97155' + str(random.randint(1000000, 9999999))
        self.client.post(endpoints['send_otp'], headers=headers,
                         json={"phoneNumber": self.phone_number,
                               "isForLogin": False})
        try:
            signup_resp = self.client.post(endpoints['new_signup'], headers=headers,
                                           json={"phoneNumber": self.phone_number,
                                                 "otp": 102030,
                                                 "email": f"test{self.phone_number}@rizek.com",
                                                 "fullName": f"test{self.phone_number}",
                                                 "device": {
                                                     "deviceId": "",
                                                     "appsFlyerId": 12,
                                                     "os": "ios",
                                                     "appVersion": "v1",
                                                     "appId": 123,
                                                     "longitude": 12.12,
                                                     "latitude": 12.12,
                                                     "token": "test"
                                                 }
                                                 })
            print(signup_resp.text)
            self.token = signup_resp.json()['data']['token']
        except KeyError:
            login_resp = self.client.post(endpoints['new_login'], headers=headers,
                                          json={"appId": 1,
                                                "appVersion": "1.3.3",
                                                "appsFlyerId": "1592980031887-8241865492952709319",
                                                "deviceToken": "cTxsiFhxRJaUCRYGyMxkIN:APA91bH6WJom5PHNS82Bpf0HS8PIzFfgmTf8qRG8W6EFcxE8wDLIgKc1fC0XVoF559TCh0As3pv2XH08pZTDHZs9qKA_LY0PmBkIn1Go4hA_uf1sCWCu7i9QsXEkeZ78tOhXi5A0Y4eb",
                                                "deviceId": "d319cd8b521f1957",
                                                "latitude": 20.12,
                                                "longitude": 80.123,
                                                "os": "android",
                                                "otp": 102030,
                                                "phoneNumber": self.phone_number
                                                })
            print(login_resp.text)
            self.token = login_resp.json()['data']['token']
        self.headers = {k: v for k, v in headers.items()}
        self.headers['Authorization'] = f'Bearer {self.token}'

    wait_time = between(1, 4)
    host = 'https://testapi.rizek.com/v1/api'
    tasks = [RizekAuthTaskSet]
