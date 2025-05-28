import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()


def check_api_status(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Возбуждаем HTTPError для неудачного запроса (4xx or 5xx)
        print(f"API {url} is up and running. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"API {url} is down or unreachable. Error: {e}")


def main():
    api_url = os.environ.get(
        "API_URL", "http://localhost:8000/api/"
    )
    while True:
        check_api_status(api_url)
        time.sleep(60)


if __name__ == "__main__":
    main()
