#!/usr/bin/env bash

# runner.sh
# this maps environment variables to runner.py args
# so we can run it within Docker with params set as env vars
# TODO check for existence of each env var
# TODO trap errors

LOGFILE="$OUTPUT_FILE".log

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

# only use args if they have corresponding env var set, otherwise let py script use defaults
# accumulate ARGS for the vars with default that are set
# this will be valuable for quick testing
ARGS=""
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


# get system stats in logfile
echo "System Memory State " >> $LOGFILE
vmstat -s -S M >>$LOGFILE
# also send it to the error log?
>&2 vmstat -s -S g
RUNCMD="runner.py $ARGS -d $DATA_PATH --cross_validation $GENE_FILE "
echo $RUNCMD >>$LOGFILE
echo "STARTED `date +'%d/%m/%Y %H:%M:%S'`" >>$LOGFILE
python $RUNCMD > "$OUTPUT_FILE" 2>> "$LOGFILE"
PYTHON_EXITCODE=$?
if [ $PYTHON_EXITCODE -eq 0 ]
then
  echo "COMPLETED `date +'%d/%m/%Y %H:%M:%S'`" >>$LOGFILE
else
  echo "ERROR `date +'%d/%m/%Y %H:%M:%S'` exit code $PYTHON_EXITCODE" >>$LOGFILE
fi


# function to show an example run on a laptop with HPCC mounted, and will output to the screen. Note this is not run when the script is run
example_run ()
{
    DATA_PATH=/Volumes/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend2 \
    GENE_FILE="../input_genes_newlines.txt" \
    GP_NET_TYPE="BioGrid" GP_FEATURES="Embedding" GP_GSC="GO" JOBNAME="example_run" \
    python runner.py --net_type $GP_NET_TYPE --features $GP_FEATURES --GSC $GP_GSC -d "$DATA_PATH" -j "$JOBNAME" --cross_validation "$GENE_FILE"

}