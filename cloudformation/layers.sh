#!/bin/bash

docker pull gemerick/developmentseed-geolambda:2.0.0
docker pull gemerick/developmentseed-geolambda-py:2.0.0

mkdir -p deploy/gdal
docker run --rm -v $PWD/deploy/gdal:/home/geolambda -t gemerick/developmentseed-geolambda:2.0.0 package.sh
mv deploy/gdal/lambda-deploy.zip deploy/lambda-gdal-layer.zip

mkdir -p deploy/py
docker run --rm -v ${PWD}/deploy/py:/home/geolambda -t gemerick/developmentseed-geolambda-py:2.0.0 package-python.sh
mv deploy/py/lambda-deploy.zip deploy/lambda-py-layer.zip
