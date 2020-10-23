FROM osgeo/gdal:alpine-normal-3.0.4
MAINTAINER "Team America"

RUN apk add --update bash
RUN apk add --update python3-dev
RUN apk add --update alpine-sdk
RUN apk add --update libxslt-dev && apk add --update libxml2-dev && apk add --update jpeg-dev

RUN mkdir /extractor
COPY ./requirements.txt /extractor
RUN sh -x \
    && pip3 install --upgrade pip \
    && pip3 install -r /extractor/requirements.txt \
    && pip3 install gunicorn   
COPY ./extractor /extractor
COPY ./env.cfg /extractor/env.cfg

EXPOSE 8080

ENV EXTRACTOR_CONFIG_FILE=/extractor/env.cfg

WORKDIR "/"
# TODO: Test if we can safely run with gevent mode (need to ensure threadsafety of gdal extensions for now run in worker mode
CMD [ "gunicorn", "-w 4", "-b :8080", "--timeout=180", "extractor:create_app()" ]