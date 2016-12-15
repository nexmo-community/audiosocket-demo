import logging
import os


class Config(object):
    def __init__(self):
        self.missing_keys = []
        self.api_key = self._load('API_KEY')
        self.api_secret = self._load('API_SECRET')
        self.app_id = self._load('APP_ID')
        self.private_key = self._load('PRIVATE_KEY')
        self.phone_number = self._load('PHONE_NUMBER')
        self.host = self._load('HOST')
        self.port = self._load('PORT', 8000)

    def _load(self, key, default=None):
        val = os.getenv(key, default)
        if val is None:
            self.missing_keys.append(key)
            logging.error("Missing environment variable %s", key)
        return val

    @property
    def fully_configured(self):
        return not self.missing_keys
