# OctoPrint-Wyze

OctoPrint-Wyze lets you control and automate Wyze home devices through OctoPrint. You can register plugs, lights and cameras to turn on or off whenever specific events occur. For example, you can set a light to turn on whenever the web client is opened, or a print or timelapse is started, then off when a print has finished.

NOTE: Only Python 3.8 and up will work! This is not ideal since OctoPrint does not officially support anything higher than Python 3.7 at the moment, so you will need to be comfortable updating OctoPrint's Python environment. This is a hard requirement because the wyze_sdk module that this plugin relies on will only work with Python 3.8 and up.

![OctoPrint-Wyze Screenshot](/OctoPrint-Wyze.png)

## Setup

Ensure that OctoPrint is running Python 3.8 or higher. If you're not already sure about this, it probably isn't. But OctoPrint's Python version can be found at the bottom left of the web client.

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/eshapiro42/OctoPrint-Wyze/archive/main.zip

## Configuration

Add your Wyze username and password in the plugin settings and reload the server. 

NOTE: Your username and password will be stored in plain text in OctoPrint's config.yaml file, so if other people have access to your server and you don't want them to have this information then do not use this plugin.
