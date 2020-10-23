#!/bin/sh -e

APP=extractor

# stop bash from expanding on anything other than a line return. This is needed for properties that contain a space
export IFS=$'\n'

if [ -z $1 ] || [ -z $2 ]
then
    echo "Usage: $(basename $0) <ENV:dev|uc> <cloudformation s3 bucket>"
    exit
fi
ENV=$1
BUCKET=$2

if [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac OSX
    SCRIPT=${BASH_SOURCE[0]}
    CLOUDFORMATION_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P)
else
    # Unknown.
    SCRIPT=$(readlink -f "$0")
    CLOUDFORMATION_DIR=$(dirname "$SCRIPT")
fi
BASEDIR=$CLOUDFORMATION_DIR/..
DEPLOY_DIR=$BASEDIR/deploy

mkdir -p $DEPLOY_DIR

PARAMS=`cat $CLOUDFORMATION_DIR/$APP.$ENV.params | grep -v '^#' | sed -e 's/\n/ /'`
TAGS=`cat $CLOUDFORMATION_DIR/$APP.$ENV.tags | grep -v '^#' | sed -e 's/\n/ /'`

if [[ $3 == 'build' ]]
then
    cd $BASEDIR
    #Clean up first
    rm -rf $DEPLOY_DIR/extractor.zip

    zip -rq $DEPLOY_DIR/extractor.zip extractor
    cd $BASEDIR/venv/lib/python3.*/site-packages
    zip -qr $DEPLOY_DIR/extractor.zip * -x "*boto*"
    cd $CLOUDFORMATION_DIR
fi

aws cloudformation package --template-file $CLOUDFORMATION_DIR/$APP-cfn.yaml --s3-bucket $BUCKET --output-template-file $DEPLOY_DIR/$APP.out.yaml

aws cloudformation deploy --template-file $DEPLOY_DIR/$APP.out.yaml --stack-name $APP --capabilities CAPABILITY_IAM --parameter-overrides $PARAMS --tags $TAGS
