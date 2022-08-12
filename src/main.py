import asyncio
import logging
import os
from threading import Thread

import requests
import uvicorn
from fastapi import FastAPI


LOGGER = logging.getLogger(__name__)


try:
    CLIENT_ID = os.environ["CLIENT_ID"]
    CLIENT_SECRET = os.environ["CLIENT_SECRET"]
except KeyError as e:
    error_message = f"missing environment variable: {e}"
    LOGGER.critical(error_message)
    raise RuntimeError(error_message) from e


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Server is ready"}


def _callback_blocking(code: str):
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        params={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": "http://localhost:8000/callback",
        },
        headers={"Accept": "application/json"},
    )
    return response


@app.get("/callback")
async def callback(code: str):
    # asynchronously call _callback_blocking
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, _callback_blocking, code)
    # check the response
    if response.status_code != 200:
        LOGGER.error(f"failed to get access token:\n{response}")
        return {"message": "failed to get access token"}
    # get the token
    access_token = response.json()
    access_token_message = f"access token: {access_token}"
    LOGGER.critical(access_token_message)
    print(access_token_message)
    return {"message": "Authentication complete; view application logs for token"}


if __name__ == "__main__":
    server_thread = Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": "localhost", "port": 8000},
        daemon=True
    )
    server_thread.start()
    _ = input("\nPress enter when the server is ready...\n")
    print("go to this website to authenticate:")
    print(f"https://github.com/login/oauth/authorize?scope=user:email&client_id={CLIENT_ID}")
    _ = input("\nPress enter to close\n")
