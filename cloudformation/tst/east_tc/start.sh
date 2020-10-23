#!/bin/bash -xe

# Set Environment Variables
PATH=/usr/local/bin:$PATH
IMG_NAME="ods/extractor:latestTcTst"
MACH_NAME="extractor"

mkdir -p /app

# Install Docker
yum install docker -y
mv /var/lib/docker /app/docker
ln -s /app/docker /var/lib/docker
systemctl enable docker
systemctl start docker

# Copy the Docker image to machine, uncompress and load
aws s3 cp s3://ods-sa-t1/Reservoir_Dogs/Diode_Transfer_Service/UC-TC/jenkins/artifacts/builds/deploy/ods-extractor/tc/extractor-TC-TST.tgz /app/app.tgz --no-verify-ssl --region us-iso-east-1 

/usr/bin/gunzip -c /app/app.tgz | /usr/bin/docker load

# Run Docker Machine
/usr/bin/docker run --name ${MACH_NAME} -p 80:8080 -d --restart always --log-driver syslog ${IMG_NAME}
