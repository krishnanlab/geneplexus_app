# test/test_runner_sh.sh
# sets variables from an azure env file, and starts runner.sh, which is what calles the
# python pipeline runnger (runner.py)  in the docker container to run jobs
# this is to test runner.sh, not runner.py 

# # usage
# # make sure to activate your python environment prior to running
# # and have all the backend files that are needed available. 
# conda activate geneplexus_app
# # then run this test 
# ./test_runner_sh.sh



GPDIR=$HOME/docs/geneplexus_app
TESTDIR=$GPDIR/test

source $TESTDIR/testenv  # this should have all env vars/config that gets set by the logic app that calls the container

# override default env for this test

export DATA_PATH=$HOME/tmp/geneplexus_data_backend2/
export GENE_FILE=$TESTDIR/input_genes_newlines.txt
export OUTPUT_FILE=$GPDIR/instance/runner_test_output_file.html
export JOBNAME=test_from_runner_sh

# alternatively, use --cross_validation
# overwrites any existing results file
$GPDIR/runner.sh

# python ../runner.py --net_type $GP_NET_TYPE --features $GP_FEATURES --GSC $GP_GSC -d "$DATA_PATH" -j "$JOBNAME" --no-cv  $GENE_FILE  > results.html