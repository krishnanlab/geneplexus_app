# test/test_runner_sh.sh
# sets variables from an azure env file, and starts runner.sh, which is what calles the
# python pipeline runnger (runner.py)  in the docker container to run jobs
# this is to test runner.sh, not runner.py 

# # usage
# # make sure to activate your python environment prior to running
# # and have all the backend files that are needed available and .env up to date
# conda activate <env name>
# test/test_runner_sh.sh


GPDIR=.
TESTDIR=$GPDIR/test

# this should have all env vars/config that gets set by the logic app that calls the container
source .env
# create env vars just like the job launcher would, using random job name
export DATA_PATH=$DATA_PATH
JOB_ID=$(python -c 'import uuid; print(str(uuid.uuid1())[0:8])')
export JOBNAME=test_job_${JOB_ID}
export JOB_PATH=$JOB_PATH
export GENE_FILE=$JOB_PATH/$JOBNAME/input_genes.txt
export OUTPUT_FILE=$JOB_PATH/$JOBNAME/results.html

# create job folder 
mkdir $JOB_PATH/$JOBNAME
# copy test gene set into job folder
cp $TESTDIR/input_genes_newlines.txt $GENE_FILE

# set model params 
export GP_NET_TYPE='BioGRID'
export GP_FEATURES='Embedding'
export GP_GSC='GO'
# optional  --cross_validation

export APP_POST_URL=http://localhost:5000/jobs

$GPDIR/runner.sh
