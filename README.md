# Audiosocket Demo

An app to demonstrate a Web browser playing audio from a conference using the
the Nexmo Voice API WebSockets feature and the browser Web Audio API

# Installation

You'll need Python 2.7, and we recommend you install the audiosocket demo inside
a python virtualenv. You may also need header files for Python and OpenSSL,
depending on your operating system. The instructions below are for Ubuntu 14.04.

```bash
sudo apt-get install -y python-pip python-dev libssl-dev
pip install --upgrade virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

# Configuration

The Audiosocket server is a [12-factor app](https://12factor.net/) so it can be
easily deployed via Heroku or Docker. This means it's configured using
environment variables. The following configuration values are available:

| Environment Variable | Required? | Description |
| -------------------- | --------- | ----------- |
| APP_ID | Yes | The id of your Nexmo application |
| API_KEY | Yes | Your Nexmo API key (Get from the [Nexmo Dashboard](https://dashboard.nexmo.com/settings)) |
| API_SECRET | Yes | Your Nexmo API secret (Get from the [Nexmo Dashboard](https://dashboard.nexmo.com/settings)) |
| APP_ID | Yes | The id generated when you created your Nexmo application. |
| PRIVATE_KEY | Yes | The private key generated when you created your Nexmo application. |
| PHONE_NUMBER | Yes | The Nexmo number associated with the application. |
| HOST | Yes | The hostname through which Nexmo can contact your server. (If you are using ngrok, this will look like `ABC123.ngrok.com`)
| PORT | No | The port the Audiosocket server will bind to (Default: 8000) |

You can use [Foreman](https://github.com/ddollar/foreman) or [Honcho](https://honcho.readthedocs.io/en/latest/), but we're going to
use [envdir](https://pypi.python.org/pypi/envdir) because it supports multi-line
values, and we need to supply a private key, which is quite long.

```bash
pip install envdir
mkdir config    # We'll store our config in here
```
