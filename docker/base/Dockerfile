FROM python:3.7-slim-bullseye

ARG TARGETPLATFORM

RUN apt-get update \
    && apt-get install -y --no-install-recommends apt-utils libssl-dev \
    && apt-get install -y --no-install-recommends cmake \
    && apt-get install -y --no-install-recommends curl gnupg ca-certificates zlib1g-dev libjpeg-dev \
    && apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 libxrender1 libglib2.0-bin libx265-192 \
    && apt-get install -y --no-install-recommends build-essential \
    && apt-get install -y --no-install-recommends libgstreamer1.0-0 gstreamer1.0-dev gstreamer1.0-tools \
    && apt-get install -y --no-install-recommends gstreamer1.0-plugins-base gstreamer1.0-plugins-good  \
    && apt-get install -y --no-install-recommends gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly  \
    && apt-get install -y --no-install-recommends gstreamer1.0-libav \
    && apt-get install -y --no-install-recommends gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-pulseaudio \
    && apt-get install -y --no-install-recommends libcairo2-dev libxt-dev libgirepository1.0-dev libgstrtspserver-1.0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install pycairo PyGObject

RUN if [ "$TARGETPLATFORM" = "linux/arm/v7" ]; then \
        apt-get update && \
        apt-get install -y --no-install-recommends liblcms2-2 libwebpdemux2 libaom0 libatk-bridge2.0-0 libatk1.0-0 libatlas3-base libatspi2.0-0 \
            libavcodec58 libavformat58 libavutil56 libbluray2 libcairo-gobject2 libcairo2 libchromaprint1 libcodec2-0.9 \
            libdatrie1 libdrm2 libepoxy0 libfontconfig1 libgdk-pixbuf2.0-0 libgfortran5 libgme0 libgraphite2-3 libgsm1 \
            libgtk-3-0 libharfbuzz0b libilmbase25 libjbig0 libmp3lame0 libmpg123-0 libogg0 libopenexr25 libopenjp2-7 libopenmpt0 \
            libopus0 libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 libpixman-1-0 librsvg2-2 libshine3 libsnappy1v5 libsoxr0 \
            libspeex1 libssh-gcrypt-4 libswresample3 libswscale5 libthai0 libtheora0 libtiff5 libtwolame0 libva-drm2 libva-x11-2 libva2 \
            libvdpau1 libvorbis0a libvorbisenc2 libvorbisfile3 libvpx6 libwavpack1 libwayland-client0 libwayland-cursor0 libwayland-egl1 \
            libwebp6 libwebpmux3 libx264-160 libx265-192 libxcb-render0 libxcb-shm0 libxcomposite1 libxcursor1 libxdamage1 libxfixes3 libxi6 \
            libxinerama1 libxkbcommon0 libxrandr2 libxvidcore4 libzvbi0 && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/* && \
        pip install https://www.piwheels.org/simple/numpy/numpy-1.21.4-cp37-cp37m-linux_armv7l.whl#sha256=826319c22f05d7b50c3637af5563234edbb02f5634a08d314d21ef00271a32fe \
            https://www.piwheels.org/simple/pillow/Pillow-8.3.2-cp37-cp37m-linux_armv7l.whl#sha256=8488aadaef913169c3577fd117bc3c0498adccfcd3002a475a927855c0f9167e \
            https://www.piwheels.org/simple/imutils/imutils-0.5.4-py3-none-any.whl#sha256=f233020af4b67d42caea543b8a8c9aebbb7f5159d7ef6d7dc8980282a20ade88 \
            https://www.piwheels.org/simple/opencv-python/opencv_python-4.5.5.64-cp37-cp37m-linux_armv7l.whl#sha256=5cd67e8dcf8989d86f30a4d9160ac278c1ec5a81a68df9603b9aa68c92e0170c; \
    else \
        pip install imutils==0.5.4 pillow==8.3.2 opencv-python==4.5.4.60; \
    fi
