#! /bin/bash
# test/test_runner_py.sh
# sets variables from an azure env file, and starts runner.py, directly from python
# this is to test runner.py, not runner.sh which is a layer between 
source .env 

export DATA_PATH=$DATA_PATH # from .env
export JOB_PATH=$JOB_PATH # from .env

JOB_ID=$(python -c 'import uuid; print(str(uuid.uuid1())[0:8])')
export JOBNAME=test-job-${JOB_ID}
export OUTPUT_PATH=$JOB_PATH/$JOBNAME
export GENE_FILE=$OUTPUT_PATH/input_genes.txt
export OUTPUT_FILE=$OUTPUT_PATH/results.html


# set model params 
export GP_NET_TYPE='BioGRID'
export GP_FEATURES='Embedding'
export GP_GSC='GO'

# create job folder 
mkdir $OUTPUT_PATH
# get some test data 
TESTDIR=test
cp $TESTDIR/input_genes_newlines.txt $GENE_FILE

# THE ACTUAL TEST RUN
python runner.py --output_path $OUTPUT_PATH --net_type $GP_NET_TYPE --features Embedding --GSC $GP_GSC -j $JOBNAME -d $DATA_PATH  $GENE_FILE > $OUTPUT_FILE

# optional --cross_validation $GENE_FILE 

