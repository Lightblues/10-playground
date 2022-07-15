#!/bin/bash

# from <https://github.com/HouCoder/blog/blob/master/hacking/auto-download-youtube-videos.md>
# script <https://gist.github.com/HouCoder/453f53fedaf6b729b92b2fce369c5e41>
# Use $ which youtube-dl to get the path.
youtube_dl_path=/var/services/homes/Easonshi/.local/bin/youtube-dl

# https://askubuntu.com/questions/157779/how-to-determine-whether-a-process-is-running-or-not-and-make-use-it-to-make-a-c
# https://askubuntu.com/a/157787
if ps aux | grep -v grep | grep $youtube_dl_path > /dev/null
then
    echo "youtube-dl is running"
    exit 1
fi

# Change these settings accordingly.
base_folder_video=/volume1/downloads/youtube-dl-downloads
base_folder_archive=/volume1/downloads/youtube-dl-download-archive
config_file=/volume1/downloads/youtube-dl-config.txt

download_playlist () {

    # https://stackoverflow.com/a/1401495/4480674
    current_date=`date +%Y-%m-%d`       # --%H-%M

    $youtube_dl_path \
        $1 \
        --output "${base_folder_video}/${2}/%(uploader)s_%(title)s_${current_date}.%(ext)s" \
        --download-archive ${base_folder_archive}download_arachive_${2} \
        --continue \
        --ignore-errors \
        --write-sub --write-auto-sub --sub-lang 'zh-Hans,en' \
        --format best \
        --write-thumbnail \

        # --proxy socks5://127.0.0.1:1080
        # --external-downloader aria2c
        # --external-downloader-args '-c -x 16 -k 1M'
        # --batch-file playlist.txt
    # $youtube_dl_path \
    #     $1 \
        # 1. 采用 config-file
        # --config-location $config_file

        # 2. 或者直接指定参数
}

# Change 
download_playlist "https://www.youtube.com/playlist?list=PL5KFvDJvg-PyIgYDEkR99tmx1FNsIK-fV" "ASMR"
# download_playlist "Your_unlisted_playlist_url_2" "playlist_name_2"

