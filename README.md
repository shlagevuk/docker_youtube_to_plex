# What is it?

docker_youtube_to_plex is a simple container with ffmpeg and youtube dl based on alpine. It will download videos in batch then name and move them in a way to ease their use with plex.

The entry point of the container is a python3 script that will parse a csv file containing information about channels, playlist and video you want to download.

The script will download the list of video using youtube-dl, and then format output files as
```
$PWD/channel/S0X_playlist/S0XE0Y_video_title.jpg        #portrait thumbnail
$PWD/channel/S0X_playlist/S0XE0Y_video_title-fanart.jpg #landscape thumbnail
$PWD/channel/S0X_playlist/S0XE0Y_video_title.mkv
$PWD/channel/S0X_playlist/season0X.jpg                  #portrait thumbnail for season0X
$PWD/channel/S0X_playlist/season0X-banner.jpg           #landscape thumbnail for season0X
```
With this format way of naming files and folder, plex's "[personnal media show](https://support.plex.tv/articles/200220717-local-media-assets-tv-shows/)" agent will be able sort video correctly and generate thumbnails for videos and seasons.

Thumbnails for a season are the thumbnail of the first video.

You can also add in channel's folder a `show.jpg`, `banner.jpg` and `art.jpg`. This have to be done manually as it's not automatised.

# How to use

## the csv

You need to make a csv file containing the list of channels/playlists/video you want to download.
It is formatted as follow:
```
youtube_url [channel_name] [playlist_name]
```
- `Channel_name` and `playlist_name` are optional as youtube-dl will get automatically their values. But if you want to customise them it's here
- The `youtube_url` may be almost any url of streaming service supported by youtube-dl. But the script have only be tested on youtube and dailymotion.
- **be careful:** the order of download matter for naming and download. The option `--download-archive` from youtube-dl is used by default.

### Example:
- basic example
```
chan_a_playlist_a
chan_a_playlist_b
chan_a_playlist_c
chan_b_playlist_a
chan_b
video_x misc random
video_y misc random
video_z misc random
```
will get you:
```
chan_a/S01_playlist_a/S01E01_video_title.mkv ...
chan_a/S02_playlist_b/S02E01...
chan_a/S03_playlist_c/S03E01...
chan_b/S01_playlist_a/S01E01...
chan_b/S02_upload_from_chan_b/S02E01...
misc/S01_random/S01E01_video_x_title.mkv
misc/S01_random/S01E02_video_y_title.mkv
misc/S01_random/S01E03_video_z_title.mkv
```

- This will download all video from channel_foo on the first line. Then the second line **may do nothing** if all video from playlist_bar are from channel_foo. Because all video are already in the "download-archive" file from youtube-dl. It's recommended to go from more specific to less specific.
```
url_of_channel_foo channel_foo bulk_video   
url_of_playlist_bar_from_channel_foo playlist_bar first_season
```

- This will add all video of 'mlp2' in same folder of 'mlp1' with mlp2 episode number following the last from 'mlp1'
```
url_of_playlist_mlp1 channel.mlp mlp1
url_of_playlist_mlp2 channel.mlp mlp1
```
```
channel.mlp/S01_mlp1/S01E01_video1_of_mlp1.mkv
...
channel.mlp/S01_mlp1/S01E08_video8_of_mlp1.mkv
channel.mlp/S01_mlp1/S01E09_video1_of_mlp2.mkv
...
```

## Docker command

This will run in background all download in `./youtube_to_plex.csv`. It create a `./youtube_to_plex.txt` for `--youtube-archive` output, needed output folder, a `tmp` folder and a `./YYYYMMDDhhmmss_youtube_to_plex.log`.
```bash
docker run -d --rm -u $(id -u):$(id -g) -v $PWD:/data shlagevuk/docker_youtube_to_plex
```


# TODO

- documentation for parameter of script
- improve code quality
- add option for youtube-dl
- implement options
