# test/test_runner_sh.sh
# sets variables from an azure env file, and starts runner.sh, which is what calles the
# python pipeline runnger (runner.py)  in the docker container to run jobs
# this is to test runner.sh, not runner.py 

# # usage
# # make sure to activate your python environment prior to running
# # and have all the backend files that are needed available and .env up to date
# conda activate <env name>
# test/test_runner_docker.sh 
# ghe script inside docker needs the following set

# $GENE_FILE
# $DATA_PATH
# $OUTPUT_FILE # job folder taken as the directory of this
# # OUTPUT_PATH=`dirname $OUTPUT_FILE`
# $GP_NET_TYPE
# $GP_FEATURES
# $GP_GSC
# $JOBNAME

# requires docker to be running 
if ! command -v docker &> /dev/null
then
    echo "docker could not be found"
    exit
fi

GPDIR=.
TESTDIR=$GPDIR/test

# this should have all env vars/config that gets set by the logic app that calls the container

source .env

# TODO test for basic vars are present in .env
echo "data path $DATA_PATH job_path $JOB_PATH"
echo "Note: the paths above must be in your docker config... "
# random job name
JOB_ID=$(python -c 'import uuid; print(str(uuid.uuid1())[0:8])')
export JOBNAME=docker_test_${JOB_ID}

DOCKER_STORAGE_MOUNT=/home/dockeruser
DOCKER_DATA_PATH=${DOCKER_STORAGE_MOUNT}/$(basename $DATA_PATH)/
DOCKER_JOB_PATH=${DOCKER_STORAGE_MOUNT}/$(basename $JOB_PATH)
DOCKER_OUTPUT_FILE=$DOCKER_JOB_PATH/$JOBNAME/results.html
DOCKER_GENE_FILE=$DOCKER_JOB_PATH/$JOBNAME/input_genes.txt
# export OUTPUT_FILE=$JOB_PATH/$JOBNAME/results.html

# create job folder 
mkdir $JOB_PATH/$JOBNAME
# copy test gene set into job folder
cp $TESTDIR/input_genes_newlines.txt $JOB_PATH/$JOBNAME/input_genes.txt

# set model params 
export GP_NET_TYPE='BioGRID'
export GP_FEATURES='Embedding'
export GP_GSC='GO'

# optional  --cross_validation
TAG=latest


test_docker_shell () 
{
  docker run -t -i  -v $DATA_PATH:$DOCKER_DATA_PATH -v $JOB_PATH:$DOCKER_JOB_PATH    \
    -e DATA_PATH=$DOCKER_DATA_PATH \
    -e JOB_PATH=$DOCKER_JOB_PATH/$JOBNAME \
    -e GENE_FILE=$DOCKER_GENE_FILE  \
    -e OUTPUT_FILE=${DOCKER_JOB_PATH}/${JOBNAME}/results.html \
    -e GP_NET_TYPE -e GP_FEATURES -e GP_GSC -e JOBNAME \
    geneplexus-backend:$TAG /bin/bash
}

echo starting geneplexus-backend:$TAG
docker_cmd="docker run -v $DATA_PATH:$DOCKER_DATA_PATH -v $JOB_PATH:$DOCKER_JOB_PATH  \
    -e DATA_PATH=$DOCKER_DATA_PATH \
    -e JOB_PATH=$DOCKER_JOB_PATH/$JOBNAME \
    -e GENE_FILE=$DOCKER_GENE_FILE \
    -e OUTPUT_FILE=${DOCKER_JOB_PATH}/${JOBNAME}/results.html \
    -e GP_NET_TYPE -e GP_FEATURES -e GP_GSC -e JOBNAME \
    geneplexus-backend:$TAG"

echo $docker_cmd
$($docker_cmd)
