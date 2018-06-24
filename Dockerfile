#
# Dockerfile for youtube-dl
#
FROM alpine
#MAINTAINER kev <noreply@easypi.pro>

RUN set -xe \
    && apk add --no-cache ca-certificates \
                          ffmpeg \
                          openssl \
                          python3 \
                          bash \
    && pip3 install youtube-dl

COPY ./youtube_to_plex.py /usr/local/sbin/
RUN chmod +x /usr/local/sbin/youtube_to_plex.py

WORKDIR /data

ENTRYPOINT ["youtube_to_plex.py"]
