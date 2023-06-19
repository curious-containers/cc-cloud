FROM python:3.10-bullseye

RUN pip install poetry==1.4.2 uwsgi

COPY . /cc_cloud
WORKDIR  /cc_cloud
RUN poetry install

CMD poetry run uwsgi dev/uwsgi-cloud.ini