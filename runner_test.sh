source azure/dockerenv
export DATA_PATH=/Volumes/compbio/krishnanlab/projects/GenePlexus/repos/GenePlexusBackend/data_backend 
export GENE_FILE="test/input_genes_newlines.txt" 
python runner.py --net_type $GP_NET_TYPE --features $GP_FEATURES --GSC $GP_GSC -d "$DATA_PATH" -j "$JOBNAME" --cross_validation $GENE_FILE  > test/results.html