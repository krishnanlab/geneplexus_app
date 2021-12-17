#!/usr/bin/env bash

# runner.sh
# this maps environment variables to runner.py args
# so we can run it within Docker with params set as env vars
# TODO check for existence of each env var
# TODO trap errors


# required args
if [ ! -f "$GENE_FILE" ]; then
    echo "gene file=$GENE_FILE was not found, exiting"
    exit 1
fi

if [ ! -d "$DATA_PATH" ]; then
    echo "Data path $DATA_PATH not found, exiting"
    exit 1
fi 

if [ -z "$DATA_PATH" ]; then 
    echo "DATA_PATH variable must be set to location of backend data, exiting"
    exit 1
fi

if [ -z "$OUTPUT_FILE" ]; then 
    echo "OUTPUT_FILE variable must be set for writing output, exiting"
    exit 1
fi

LOGFILE="$OUTPUT_FILE".log
OUTPUT_PATH=`dirname $OUTPUT_FILE`

# get the folder where the output file is to be saved based on output file

# only use args if they have corresponding env var set, otherwise let py script use defaults
# accumulate ARGS for the vars with default that are set
# this will be valuable for quick testing
ARGS="--output_path $OUTPUT_PATH "

if [ -n "$GP_NET_TYPE" ]; then 
    ARGS="$ARGS --net_type $GP_NET_TYPE"
fi

if [ -n "$GP_FEATURES" ]; then 
    ARGS="$ARGS --features $GP_FEATURES"
fi

if [ -n "$GP_GSC" ]; then 
    ARGS="$ARGS --GSC $GP_GSC"
fi

if [ -n "$JOBNAME" ]; then 
    ARGS="$ARGS -j $JOBNAME"
fi


function post_status ()
{
  # post-job status update
  # APP_POST_URL is set by the OS or Dockerfile
  url=$APP_POST_URL/$JOBNAME

  STATUS_DATA='{"status":'$1'}'

  curl --header "Content-Type: application/json" \
    --request POST \
    --data $STATUS_DATA \
    $url

}

# get system stats in logfile
#echo "System Memory State " | tee -a  $LOGFILE
#vmstat -s -S M  | tee -a $LOGFILE
# also send it to the error log?
# >&2 vmstat -s -S g
RUNCMD="runner.py $ARGS -d $DATA_PATH --cross_validation $GENE_FILE "
echo $RUNCMD | tee -a $LOGFILE
echo "STARTED `date +'%d/%m/%Y %H:%M:%S'`" | tee -a $LOGFILE
python $RUNCMD > "$OUTPUT_FILE" 2>  $LOGFILE
cat $LOGFILE
PYTHON_EXITCODE=$?
if [ $PYTHON_EXITCODE -eq 0 ]
then
  echo "COMPLETED `date +'%d/%m/%Y %H:%M:%S'`"  2>&1 | tee -a $LOGFILE
  post_status 200 2>&1 | tee -a $LOGFILE
 
else
  echo "ERROR `date +'%d/%m/%Y %H:%M:%S'` exit code $PYTHON_EXITCODE"  | tee -a  $LOGFILE
  post_status 500 2>&1 | tee -a $LOGFILE
fi



# testing example
# make sure to activate your python environment prior to running
function testrun ()
{
    # get data_path from your .env file
   source .env
    # change this to a gene file you have on your machine
   export GENE_FILE="../input_genes_newlines.txt" 
   export OUTPUT_FILE="../test_output.html"
   GP_NET_TYPE="BioGrid" GP_FEATURES="Embedding" GP_GSC="GO" JOBNAME="example_run"  ./runner.sh 
   # open $OUTPUT_FILE
}
    # # DATA_PATH=/Volumes/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend2 \

    # python runner.py --net_type $GP_NET_TYPE --features $GP_FEATURES --GSC $GP_GSC -d "$DATA_PATH" -j "$JOBNAME" --cross_validation "$GENE_FILE"

