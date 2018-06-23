#!/usr/bin/python3

import sys
import argparse
import csv
import subprocess
import os
import glob
import logging
import shutil
import datetime

parser = argparse.ArgumentParser(description='''
    Python script to download playlists or channel from youtube and put them in
     folders parsable by plex's custom serie agent
    It will work as follow:
    -download the playlist bestaudio+bestvideo and assemble them in .mkv file.
    -download miniatures of each video
    -put them in [output_path]/[channel_name]/S0X_[playlist_name]/E00X_[video_file_title].mp4
    -convert miniatures to match plex requierement
    ''')

parser.add_argument('-t,--target_dir', dest='target_dir', type=str, default='/data/',help='''
    target_dir is the default directory to work on for input file by default and
    output files (video and thumbnails)
    ''')
parser.add_argument('--download_archive', dest='download_archive', type=str, default='/data/youtube_to_plex.txt',help='''
    download_archive is a file created by youtube-dl to track which video have already
    been downloaded. You can bypass this restriction by using the -f option.
    output files (video and thumbnails)
    ''')
parser.add_argument('-f', dest='force', action="store_true", help='''
    force download of videos, ignoring the download-archive option of youtube-dl
    ''')
parser.add_argument('-i,--input_file', dest='input_file', type=str, default='/data/youtube_to_plex.csv', help='''
    Input file containing a list of playlist url or channel urlself, one per line.
    You can add custom naming behavior with format:
    my_url custom_channel_name custom_playlist_name
    By default it use /[target_dir]/youtube_to_plex.csv
    ''')
parser.add_argument('--sublang', dest='sublang', type=str, default='fr,en', help='''
    languages of subtitles you want to DL if available as comma separated list
    ''')
parser.add_argument('-d', dest='debug', action='store_true', help='''
    increase verbosity of logging, allow to see youtube-dl and ffmpeg output
    ''')
parser.add_argument('--log', dest='log_path', type=str, default='./'+datetime.datetime.now().strftime('%Y%m%d%H%M%S')+"_youtube_to_plex.log", help='''
    path of log file
    ''')

args = parser.parse_args()
input_file=str(args.input_file)
target_dir=str(args.target_dir)
download_archive=str(args.download_archive)
force_download=bool(args.force)
sublang=str(args.sublang)
debug=bool(args.debug)
log_path=str(args.log_path)

if debug:
    logging.basicConfig(filename=log_path,level=logging.DEBUG)
else:
    logging.basicConfig(filename=log_path,level=logging.INFO)

# Creating needed directories
if not os.path.exists(target_dir):
    logging.debug("create" + target_dir)
    os.makedirs(target_dir)
if not os.path.exists(target_dir+"tmp/"):
    logging.debug("create" + target_dir+"tmp/")
    os.makedirs(target_dir+"tmp/")

# from jaketame/logging_subprocess.py
def check_io():
       while True:
            output = process.stdout.readline().decode()
            if output:
                logging.debug(output)
            else:
                break

#fd_input_file=open(args.input_file,'r')
with open(input_file,'r', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    for row in spamreader:
        param=["","%(uploader)s","%(playlist)s"]
        for i in range(min(len(row),3)):
            logging.debug("param settint from csv: " +str(row[i])+ " " + str(i))
            param[i]=row[i]
        ytdl_url=str(param[0])
        ytdl_output_path=str(param[1]) + '/' + str(param[2]) + '/%(upload_date)s.%(title)s.%(ext)s'
        logging.info("downloaded files will be in: " + ytdl_output_path)
        logging.info("download url is: " + ytdl_url)
        if ytdl_url == "":
            logging.error("url to download empty")
            exit(1)

        cmd = [ 'youtube-dl',
                '--retries', '3',
                '--no-call-home',
                '--no-cache-dir',
                '--ignore-errors',
                '--write-info-json',
                '--write-description',
                '--write-thumbnail',
                '--write-all-thumbnails',
                '--youtube-skip-dash-manifest',
                '--sub-lang', sublang,
                '--write-auto-sub',
                '--write-sub',
                '--convert-subs', 'srt',
                '--add-metadata',
                '--embed-subs',
                '--restrict-filenames',
                '--format', 'bestvideo+bestaudio/best',
                '--merge-output-format', 'mkv',
                '--playlist-items', '1,2,3', # debug
                '--download-archive', download_archive,
                '-o', target_dir + 'tmp/' + ytdl_output_path,
                ytdl_url]
        logging.debug("command to run : " + " ".join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while process.poll() is None:
            check_io()

        #
        # Prepare to cleanup downloaded files and move folder to final destinations
        #
        channel_name=os.listdir(target_dir + 'tmp/')[0]
        playlist_name=os.listdir(target_dir + 'tmp/' + channel_name )[0]
        playlist_path=target_dir + "tmp/" + channel_name + '/' + playlist_name + '/'
        target_playlist_name=""
        target_playlist_season=0
        target_episode=0

        if os.path.exists(target_dir + channel_name):
            # does /dest/channelname/S0X_playlistname exist?
            for playlist in os.listdir(target_dir + channel_name):
                if playlist.endswith(playlist_name):
                    target_playlist_name=playlist
                    logging.info("found matching playlist : " + playlist)
                    target_playlist_season= int(target_playlist_name[1:4])

                    # if a playlist already exist it may have video in it
                    playlist_dir_list=os.listdir(target_dir + channel_name + '/' + playlist + '/')
                    if playlist_dir_list:
                        #filter item, keep ones begening with 'E'
                        playlist_dir_list_filtered= [item for item in playlist_dir_list if item.startswith('E')]
                        target_episode = int(max(playlist_dir_list_filtered)[1:4])
                        logging.info("found last episode as N°: " + str(target_episode))

            # what is the last "season" existing (S0X_channel_name)?
            if target_playlist_name == "":
                playlist_list=os.listdir(target_dir + channel_name + '/')
                if playlist_list:
                    #filter item, keep ones begening with 'S'
                    playlist_list_filtered= [item for item in playlist_list if item.startswith('S')]
                    target_playlist_season = int(max(playlist_list_filtered)[1:4])
                    logging.info("found last season as N°: " + str(target_playlist_season))

                # create /dest/channel_name/S0Y_playlist_name/ where S0Y is S0X +1
                target_playlist_name="S" + str(target_playlist_season + 1).zfill(3)+ "_" + playlist_name
                os.makedirs(target_dir + channel_name + '/' + target_playlist_name)
        else:
            # create both /dest/channel_name and /dest/channel_name/S01_playlist_name/
            os.makedirs(target_dir + channel_name)
            target_playlist_name="S" + str(target_playlist_season + 1).zfill(3)+ "_" + playlist_name
            os.makedirs(target_dir + channel_name + '/' + target_playlist_name)

        # Remove *.info.json and *.description from tmp folder
        for file in (glob.glob(playlist_path + "*.info.json") +
                    glob.glob(playlist_path + "*.description")):
            logging.debug("removing :" + file)
            os.remove(file)

        target_playlist_path=target_dir + channel_name +'/' + target_playlist_name + '/'
        target_channel_path=target_dir + channel_name +'/'

        list_of_files=  glob.glob(playlist_path + "*.mkv") + glob.glob(playlist_path + "*.mp4")
        list_of_files.sort()

        logging.debug("######\nlist of video files: "+ str(list_of_files)+ "\n######")

        for file in list_of_files:
            file_path, file_name = os.path.split(file)
            file_basename, file_ext_vid=os.path.splitext(file_name)
            file_target_name='E' + str(target_episode +1).zfill(3) + file_basename[8:]

            logging.info("generating thumbnails and renaming " + file_basename + " to "+ target_playlist_path + file_target_name)
            # moving video file
            os.rename(file, target_playlist_path + file_target_name + file_ext_vid)
            # generating thumbnails
            cmd_ffmpeg_thumbnail = ['ffmpeg', '-y', '-i', file_path + '/' + file_basename+'.jpg', '-vf', 'scale=600:-1,pad=600:800:0:(oh-ih)/2', target_playlist_path + file_target_name + ".jpg"]
            cmd_ffmpeg_thumbnail_fanart = ['ffmpeg', '-y', '-i', file_path + '/' + file_basename+'.jpg', '-vf', 'scale=-1:600', target_playlist_path + file_target_name + "-fanart.jpg"]

            process = subprocess.Popen(cmd_ffmpeg_thumbnail, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while process.poll() is None:
                check_io()
            process = subprocess.Popen(cmd_ffmpeg_thumbnail_fanart, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while process.poll() is None:
                check_io()

            # If we are at E001 we use thumbnails for the whole "Season"
            if target_episode == 0:
                logging.info("Copiing first episode thumbnails for season thumbnails")
                shutil.copy(target_playlist_path + file_target_name + ".jpg",target_playlist_path + "Season" + str(target_playlist_season + 1).zfill(3) + ".jpg")
                shutil.copy(target_playlist_path + file_target_name + "-fanart.jpg",target_playlist_path + "Season" + str(target_playlist_season + 1).zfill(3) + "-banner.jpg")
            target_episode+=1

        shutil.rmtree(target_dir + "tmp/" + channel_name )
