# test/test_runner_py.sh
# sets variables from an azure env file, and starts runner.py, which is what runs the 
# pipeline in the docker container to run jobs
# this is to test runner.py, not runner.sh (env to cli param translater)
source testenv 

export DATA_PATH=/mnt/home/billspat/tmp/geneplexus_data_backend2/
export GENE_FILE=input_genes_newlines.txt
# alternatively, use --cross_validation
# overwrites and existing results file
python ../runner.py --net_type $GP_NET_TYPE --features $GP_FEATURES --GSC $GP_GSC -d "$DATA_PATH" -j "$JOBNAME" --no-cv  $GENE_FILE  > results.html