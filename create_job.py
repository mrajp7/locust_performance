import inspect
import random
from datetime import datetime, timedelta
from uuid import uuid1
from locust import HttpUser, task, between, TaskSet


BASE_URL = "https://testapi.rizek.com/v1/api"

endpoints = {
    "new_signup": "/auth/signup",
    "send_otp": "/auth/sendOTP",
    "new_login": "/auth/login/phone",
    "user_exists": "/auth/isUserExists",
    "logout": "/client/auth/logout",
    'service_tree': "/cac/operating/services_tree?cityId=1",
    "create_new_job": "/client/jobs",
    "list_all_jobs": "/client/jobs/job",
    "get_card_by_id": "/payments/cards/{id}",
    "list_cards": "/payments/cards",
    "delete_card": "/payments/cards/{id}",
    "create_card": "/payments/cards"
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
                         json={"phoneNumber": self.user.phone_number},name="user_exists")

    @task(10)
    def service_tree(self):
        self.client.get(get_url(), headers=headers,name="get_service_tree")

    @task(5)
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
                               },name="create_new_job")

    @task(5)
    def list_all_jobs(self):
        resp = self.client.get(get_url(), headers=self.user.headers,name="list_all_jobs")
        print(self.user.phone_number, len(resp.json()['data']['upcoming']))

    @task(2)
    def get_card_by_id(self):
        url = get_url()
        try:
            url = url.format(id=self.user.card_ids[-1])
        except IndexError:
            return
        self.client.get(url, headers=self.user.headers,
                        name='/payments/cards/id=[id]')

    @task(2)
    def list_cards(self):
        self.client.get(get_url(), headers=self.user.headers,name="list_cards")

    @task
    def create_card(self):
        create_card_resp = self.client.post(get_url(), headers=self.user.headers,
                                            json={"cardToken": str(uuid1()),
                                                  "cardholderName": "Test Customer",
                                                  "expiry": "2025-04",
                                                  "maskedPan": "401200******1112",
                                                  "scheme": "Visa"
                                                  },name="create_card")
        try:
            self.user.card_ids.append(
                create_card_resp.json()['data']['cardId'])
        except KeyError:
            pass

    @task
    def delete_card(self):
        url = get_url()
        try:
            url = url.format(id=self.user.card_ids[-1])
            self.user.card_ids = self.user.card_ids[:-1]
        except IndexError:
            return
        self.client.delete(url, headers=self.user.headers,
                           name='/payments/cards/id=[id]')


class RizekUser(HttpUser):
    def __init__(self, env) -> None:
        super().__init__(env)
        self.phone_number = '+97155' + str(random.randint(1000000, 9999999))
        self.card_ids = []
        self.client.post(endpoints['send_otp'], headers=headers,
                         json={"phoneNumber": self.phone_number,
                               "isForLogin": False},name='send_tp')
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
                                                 },name='signup')
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
                                                },name='login')
            print(login_resp.text)
            self.token = login_resp.json()['data']['token']
        self.headers = {k: v for k, v in headers.items()}
        self.headers['Authorization'] = f'Bearer {self.token}'

    wait_time = between(1, 4)
    host = 'https://testapi.rizek.com/v1/api'
    tasks = [RizekAuthTaskSet]
