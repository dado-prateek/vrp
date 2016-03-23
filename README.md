## Grabber for virtualrealporn.com videos

By default grabs videos in 3200×1600 High and 1080p formats. May be extend by adding appropriate XPaths.

### Requirements:
 * python3
 * lxml
 * requests

### How to use:
* Login into site via browser and fill the `cookies/vrp-cookies.json` file with cookies data.
* Create dirs:
```
cd vrp
mkdir {videos,log}
```
* Run grabber:
```
./grabber.py
```

