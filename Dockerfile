FROM python:3.9

ARG WITH_CUDA=

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./src /code
COPY ./.env /.env
RUN [ -n "$WITH_CUDA" ] && sed -i '1d' /code/requirements.txt || true

RUN apt update -y
# aeneas deps
RUN apt install -y ffmpeg espeak espeak-data libespeak1 libespeak-dev
RUN apt clean && rm -rf /var/lib/apt/lists/*
# first line makes torch install without cuda
# for local environment and tests
RUN pip install --no-cache-dir --upgrade uv
RUN uv pip install --no-cache-dir --upgrade --system -r /code/requirements.txt
# this needs to be separate uv can't install this
RUN pip install --no-cache-dir --upgrade aeneas

EXPOSE 8000

CMD ["uvicorn", "api_routes:app", "--host", "0.0.0.0", "--port", "8000"]
