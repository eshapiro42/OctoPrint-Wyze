# OctoPrint-Wyze

`OctoPrint-Wyze` lets you control and automate Wyze home devices through OctoPrint. You can register plugs, lights and cameras to turn on or off whenever specific events occur. For example, you can set a light to turn on whenever the web client is opened, or a print or timelapse is started, then off when a print has finished.

![OctoPrint-Wyze Screenshot](/OctoPrint-Wyze.png)

| :warning: This plugin relies on the reverse-engineered [`wyze_sdk`](https://github.com/shauntarves/wyze-sdk/) module and will break if Wyze makes significant changes to their API or otherwise renders it unusable. |
| --- |

## Setup

Ensure that OctoPrint is running Python 3.8 or higher. If you're not already sure about this, it probably isn't. But OctoPrint's Python version can be found at the bottom left of the web client.

If you are running OctoPi and had to build Python 3.8+ from source, make sure you can import `sqlite3`. Otherwise, run `sudo apt install libsqlite3-dev` and then rebuild Python with `./configure --enable-loadable-sqlite-extensions && make`.

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/eshapiro42/OctoPrint-Wyze/archive/main.zip

## Configuration

Add your Wyze username and password in the plugin settings and reload the server. 

| :warning: Your Wyze username and password are encrypted by the plugin before being stored on your filesystem, but can be decrypted with relative ease by anyone on your system with access to OctoPrint's `config.yaml` file. Please ensure that you're taking appropriate precautions and not reusing passwords between sites! |
| --- |
