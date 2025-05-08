FROM python:3.8

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install --no-cache-dir --upgrade demucs

COPY ./src /code
EXPOSE 8000

CMD ["uvicorn", "api_routes:app",  "--host", "0.0.0.0", "--port", "8000"]