# ODS Extractor Service

Attempts to extract metadata from an object in S3, and return it as a JSON object.

## Building & Debugging

This can be run in a development environment using the `run.py` script. To run it outside of Docker -

1. Create a virtual environment (assuming python3), and install the requirements -

   ```bash
   $ python -m venv venv ./venv
   $ . ./venv/bin/activate
   $ pip install --upgrade pip
   $ pip install -r requirements.txt
   ```

2. GDAL is commented out of the `requirements.txt` intentionally, as we want to use a newer GDAL (preferably 3.0.4). This is left as an exercise for the reader.

3. Create a configuration file, and set the `EXTRACTOR_CONFIG_FILE` environment variable (see the section on [Configuration](#Configuration) options for full details) -

   ```bash
   $ touch ./env.cfg
   $ export EXTRACTOR_CONFIG_FILE=$PWD/env.cfg
   ```

4. To test the extractor(s), you can use the unit tests in `tests`

   ```bash
   $ python -m unittest discover ./tests
   ```

5. To run the service as a standalone instance
   ```bash
   $ python run.py
   ```

## Configuration

Configuration can be controlled through either a configuration file, or through environment variables (both with the same names).

```python
# Controls flask debugging, should always be False in production
FLASK_DEBUG=False

# Flask port number (only used in run.py, for docker port is controlled by gunicorn
PORT=8080
# Amazon Key Id
AKID=**************************
# Amazon Secret Key
ASAK=**************************
# Amazon region
AR='us-west-2',
# Amazon S3 Endpoint
AS3EP='s3.amazonaws.com'

# Loglevel for extractor service logs (DEBUG, INFO, WARNING, ERROR)
LOGLEVEL='INFO'
```

## Docker

1. To build

   ```bash
   $ docker build -t local/extractor:latest .
   ```

2. To run (you need to either map in a config file, or pass in environment variables for the options)
   ```bash
   docker run --name extractor-service -v $(pwd)/env.cfg:/extractor/env.cfg -p 80:8080 -d local/extractor:latest
   ```

## TODO

- Determine whether or not MRSID support is required

## Lambda

To run as an AWS Lambda gdal and python layers are required.

https://github.com/developmentseed/geolambda

Currently using version 2.0.0

One of the below Layer steps must be used to create layer zip files in the deploy folder prior to deploy.

### Deploy

The cloudformation stack can be deployed with a script

    cd cloudformation
    ./deploy.sh <env> <s3-bucket>

The env must have a cooresponding params file. The s3 bucket is for pushing the layer and code zip files.

### Layer: Use pre-built docker images

Images were built and pushed to docker hub with python 3.6.1. These can be used to build layer packages easily.

The recipe is in `cloudformation/layers.sh`

### Layer: Build

Build the gdal layer by following the 'Create a new version' instructions.
Build the python layer with these instructions: https://github.com/developmentseed/geolambda/blob/master/python/README.md

For python pay close attention to the folder (pwd) the commands get executed in.
