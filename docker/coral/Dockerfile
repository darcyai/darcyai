ARG BASE_IMAGE_TAG=dev
FROM darcyai/darcyai-base:$BASE_IMAGE_TAG

RUN echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | tee /etc/apt/sources.list.d/coral-edgetpu.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -

RUN apt-get update \
    && apt-get install -y libedgetpu1-std python3-pycoral \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --extra-index-url https://google-coral.github.io/py-repo/ pycoral~=2.0
