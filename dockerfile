FROM python:3.10

#RUN apt-get update && apt-get install -y --no-install-recommends build-essential python-dev uwsgi-plugin-python3 && rm -rf /var/lib/apt/lists/*
RUN pip install poetry==1.4.2 uwsgi

COPY . /cc_cloud
WORKDIR  /cc_cloud
RUN poetry install

CMD poetry run uwsgi dev/uwsgi-cloud.ini