# OctoPrint-Wyze

`OctoPrint-Wyze` lets you control and automate Wyze home devices through OctoPrint. You can register plugs, lights and cameras to turn on or off whenever specific events occur. For example, you can set a light to turn on whenever the web client is opened, or a print or timelapse is started, then off when a print has finished.

This plugin has **no** support for camera streams or controls. This would be [very difficult](https://github.com/eshapiro42/OctoPrint-Wyze/issues/4#issuecomment-1075802410) to add. It is exclusively for automating the powering on or off of devices to coincide with the [available printer events](https://github.com/eshapiro42/OctoPrint-Wyze/blob/b2e42489d3a5bf51ef6369d570e03e22fb96dab6/octoprint_wyze/events.py#L10).

![OctoPrint-Wyze Screenshot](/OctoPrint-Wyze.png)

| :warning: This plugin relies on the reverse-engineered [`wyze_sdk`](https://github.com/shauntarves/wyze-sdk/) module and will break if Wyze makes significant changes to their API or otherwise renders it unusable. |
| --- |

## Setup

Ensure that OctoPrint is running Python 3.8 or higher. OctoPrint's Python version can be found at the bottom left of the web client.

If you are running OctoPi and had to build Python 3.8+ from source, make sure you can import `sqlite3`. Otherwise, run `sudo apt install libsqlite3-dev` and then rebuild Python with `./configure --enable-loadable-sqlite-extensions && make`.

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/eshapiro42/OctoPrint-Wyze/archive/main.zip

## Configuration

Generate a Wyze API key and key ID here: https://developer-api-console.wyze.com/#/apikey/view.

Add your Wyze username, password, API key and key ID (generated in the previous step) in the plugin settings and reload the server. 

| :warning: Your Wyze username and password are encrypted by the plugin before being stored on your filesystem, but can be decrypted with relative ease by anyone on your system with access to OctoPrint's `config.yaml` file. Please ensure that you're taking appropriate precautions and not reusing passwords between sites! |
| --- |
