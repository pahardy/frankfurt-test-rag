"""Centralised environment and SSL setup. Import this before any API calls."""

import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH, override=True)

# Point the SSL library at the local cert bundle (needed on corporate networks).
cert_file = os.getenv("SSL_CERT_FILE")
if cert_file:
    os.environ["SSL_CERT_FILE"] = cert_file
    os.environ["REQUESTS_CA_BUNDLE"] = cert_file
