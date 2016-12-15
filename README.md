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
| API_KEY | Yes | Your Nexmo API key (Get from the [Nexmo Dashboard](https://dashboard.nexmo.com/settings)) |
| API_SECRET | Yes | Your Nexmo API secret (Get from the [Nexmo Dashboard](https://dashboard.nexmo.com/settings)) |
| APP_ID | Yes | The id generated when you created your Nexmo application. |
| PRIVATE_KEY | Yes | The private key generated when you created your Nexmo application. |
| PHONE_NUMBER | Yes | The Nexmo number associated with the application. |
| HOST | Yes | The hostname through which Nexmo can contact your server. (If you are using ngrok, this will look like `ABC123.ngrok.com`)
| PORT | No | The port the Audiosocket server will bind to (Default: 8000) |

## Configuring envdir

You can use [Foreman](https://github.com/ddollar/foreman) or [Honcho](https://honcho.readthedocs.io/en/latest/), but we're going to
use [envdir](https://pypi.python.org/pypi/envdir) because it supports multi-line
values, and we need to supply a private key, which is quite long.

`envdir` is configured by creating a directory which will contain one file per
variable. The name of each file is the name of the variable, and the contents
of the file provides the value for that environment variable.

```bash
pip install envdir
mkdir config    # We'll store our config in here
```

If you haven't already, create a Nexmo account, and then go to [the dashboard](https://dashboard.nexmo.com/settings). At the bottom of the settings
page, you should see your API key and API secret. Paste each of these into
files respectively called `config/API_KEY` and `config/API_SECRET`.

## Hostname & Port

Your audiosocket server needs to be available on a publicly hosted server. If
you want to run it locally, we recommend running [ngrok](https://ngrok.com/) to
create a publicly addressable tunnel to your computer.

Whatever public hostname you have, you should enter it into `config/HOST`.
You'll also need to know this hostname for the next step, creating a Nexmo
application.

The `PORT` configuration variable is only required if you don't want to host on
port 8000. If you're running ngrok and you're not using port 8000 for anything
else, just run `ngrok http 8000` to tunnel to your Audiosocket service.

## Creating an application and adding a phone number

Use the [Nexmo command-line tool](https://github.com/Nexmo/nexmo-cli) to create
a new application and associate it with your server (substitute YOUR-HOSTNAME
with the hostname you've put in your `HOST` config file):

```bash
nexmo app:create "Audiosocket Demo" "https://YOUR-HOSTNAME/ncco" "https://YOUR-HOSTNAME/event"
```

If it's successful, the `nexmo` tool will print out the new app ID and a
private key. Put these, respectively in `config/APP_ID` and
`config/PRIVATE_KEY`.

If you need to, find and buy a number:

```bash
# Skip the first 2 steps if you already have a Nexmo number to use.

# Replace GB with your country-code:
nexmo number:search GB —voice

# Find a number you like, then buy it:
nexmo number:buy [NUMBER]

# Associate the number with your app-id:
nexmo link:app [NUMBER] [APPID]
```

Paste the phone number into `config/PHONE_NUMBER`.

At the end of this, your config directory should look something like this:

```text
config/
├── API_KEY
├── API_SECRET
├── APP_ID
├── HOST
├── PHONE_NUMBER
└── PRIVATE_KEY
```

Now you can run the audiosocket service with:

```bash
envdir config ./venv/python server.py
```
