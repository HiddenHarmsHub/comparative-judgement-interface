import os

from dotenv import load_dotenv
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from comparison_interface import create_app

load_dotenv()

subdomain = os.getenv("SUBDOMAIN", "")

if subdomain == "":
    app = create_app()
else:
    app = DispatcherMiddleware(None, {subdomain: create_app()})
