echo "Post Build and Scan"

echo "Setting local variables"
export WRK_DIR="app"
export ENV_FILE="env.cfg"

export IMG_NAME="ods/extractor:latestUcOps"
export MACH_NAME="extractor-uc-ops"
export ARCHIVE_NAME="extractor-UC-OPS.tgz"

export BCKT_EAST="ods-sa-o1"
export BCKT_WEST="ods-sa-o2"
######################################################################
######### ONLY MODIFY THINGS BELOW HERE WITH EXTREME CAUTION #########
######################################################################
# echo "Checking Existence of the Working Directory and expand Acrhive"
# if [ ! -d "${WRK_DIR}" ]; then
#   mkdir ${WRK_DIR}
# fi
echo "Expand Archive"
tar xvfz ${WRK_DIR}.tar
echo ""
echo ""
echo ""
echo "Creating Env File"
echo "# Controls flask debugging, should always be False in production" > ${ENV_FILE}
echo "FLASK_DEBUG=False" >> ${ENV_FILE}
echo " " >> ${ENV_FILE}
echo "# Flask port number (only used in run.py, for docker port is controlled by gunicorn" >> ${ENV_FILE}
echo PORT=8080 >> ${ENV_FILE}
echo " " >> ${ENV_FILE}
echo "# Amazon region" >> ${ENV_FILE}
echo AR="'$AR'" >> ${ENV_FILE}
echo " " >> ${ENV_FILE}
echo "# Amazon S3 Endpoint" >> ${ENV_FILE}
echo AS3EP="'$AS3EP'" >> ${ENV_FILE}
echo " " >> ${ENV_FILE}
echo "# Amazon Secret Key" >> ${ENV_FILE}
echo ASAK="'$ASAK'" >> ${ENV_FILE}
echo " " >> ${ENV_FILE}
echo "# Amazon Key Id" >> ${ENV_FILE}
echo AKID="'$AKID'" >> ${ENV_FILE}
echo " " >> ${ENV_FILE}
echo "# Loglevel for extractor service logs (DEBUG, INFO, WARNING, ERROR)"  >> ${ENV_FILE}
echo "LOGLEVEL='INFO'" >> ${ENV_FILE}
echo ""
echo ""
echo ""
ls -lrta
echo ""
echo ""
echo ""
echo "Building Docker"
docker build -t ${IMG_NAME} .
echo ""
echo ""
echo ""
echo "Running Docker"
docker run --name ${MACH_NAME} -d ${IMG_NAME}
echo ""
echo ""
echo ""
echo "Environment File is: "
docker exec ${MACH_NAME} sh -c 'more /extractor/env.cfg'
echo ""
echo ""
echo ""
#Run the Unit and Postman/Newman tests
echo "Running Unit and Newman Tests"
#docker exec extractor-uc-ops bash -c 'cd /extractor; nose2 > nose2 --plugin nose2.plugins.junitxml --junit-xml'
#docker exec extractor-uc-ops bash -c 'newman run -e /extractor/test/local.postman_environment.json /extractor/test/guid.postman_collection.json > /extractor/test/newman.out'
#Copy Reports to Jenkins Server
echo "Copying Junit Reports"
#docker cp extractor-uc-ops:/extractor/nose2-junit.xml nose2-junit.xml
echo ""
echo ""
echo ""
echo "Saving Image for Archive"
docker save ${IMG_NAME} | gzip > ${ARCHIVE_NAME}
echo ""
echo ""
echo ""
echo "Uploading Artifacts to Jenkins Bucket for Cloudformation"
export AWS_DEFAULT_REGION=us-west-2
aws s3 cp ${ARCHIVE_NAME} s3://${BCKT_EAST}/jenkins/artifacts/builds/deploy/ods-extractor/uc/${ARCHIVE_NAME}
aws s3 cp cloudFormation/ops/east_uc/start.sh s3://${BCKT_EAST}/jenkins/artifacts/builds/deploy/ods-extractor/uc/start.sh
aws s3 cp cloudFormation/ops/east_uc/UC_EAST.yaml s3://${BCKT_EAST}/jenkins/artifacts/builds/deploy/ods-extractor/uc/UC_EAST.yaml

aws s3 cp ${ARCHIVE_NAME} s3://${BCKT_WEST}/jenkins/artifacts/builds/deploy/ods-extractor/uc/${ARCHIVE_NAME}
aws s3 cp cloudFormation/ops/west_uc/start.sh s3://${BCKT_WEST}/jenkins/artifacts/builds/deploy/ods-extractor/uc/start.sh
aws s3 cp cloudFormation/ops/west_uc/UC_WEST.yaml s3://${BCKT_WEST}/jenkins/artifacts/builds/deploy/ods-extractor/uc/UC_WEST.yaml

#Clean up on build server
echo "Cleaning up Build Server and workspace"
docker rm -f ${MACH_NAME}
echo "All Clean"
echo "Have a nice day"
