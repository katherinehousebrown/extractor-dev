#!/bin/bash -xe

# Set Environment Variables
PATH=/usr/local/bin:$PATH

IMG_NAME="ods/extractor:latestUcTst"
MACH_NAME="extractor"

# Install Docker
yum install docker -y
systemctl enable docker
systemctl start docker

# Copy the Docker image to machine, uncompress and load
mkdir -p /app
aws s3 cp s3://ods-sa-t1/jenkins/artifacts/builds/deploy/ods-extractor/uc/extractor-UC-TST.tgz /app/app.tgz
/usr/bin/gunzip -c /app/app.tgz | /usr/bin/docker load

# Run Docker Machine
/usr/bin/docker run --name ${MACH_NAME} -p 80:8080 -d --restart always --log-driver syslog ${IMG_NAME}
