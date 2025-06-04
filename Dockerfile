FROM python:3.9

ARG WITH_CUDA=
# Just in case (TM)
ENV UV_HTTP_TIMEOUT=120

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./src /code
COPY ./.env /.env
RUN [ -n "$WITH_CUDA" ] && sed -i '1d' /code/requirements.txt || true

RUN apt update -y
# aeneas deps
RUN apt install -y ffmpeg espeak espeak-data libespeak1 libespeak-dev

# chromedriver installation (almost) from
# https://datawookie.dev/blog/2023/12/chrome-chromedriver-in-docker/
RUN apt-get update -qq -y && \
    apt-get install -y \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-4-1 \
        libnss3 \
        xdg-utils \
        chromium \
        wget && \
    wget -q -O chromedriver-linux64.zip https://bit.ly/chromedriver-linux64-121-0-6167-85 && \
    unzip -j chromedriver-linux64.zip chromedriver-linux64/chromedriver && \
    rm chromedriver-linux64.zip && \
    mv chromedriver /usr/local/bin/

RUN apt clean && rm -rf /var/lib/apt/lists/*
# first line makes torch install without cuda
# for local environment and tests
RUN pip install --no-cache-dir --upgrade uv
RUN uv pip install --no-cache-dir --upgrade --system -r /code/requirements.txt
# this needs to be separate uv can't install this
RUN pip install --no-cache-dir --upgrade aeneas

EXPOSE 8000

CMD ["uvicorn", "api_routes:app", "--host", "0.0.0.0", "--port", "8000"]
