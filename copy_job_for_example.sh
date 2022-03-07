#!/usr/bin/env bash

# this will take an existing job and put it as the example 
# this assumes the env var $JOB_PATH is set ( use source .env to set it )
# check for parameter
export EXAMPLEJOB=$1
export EXAMPLENAME="example ( Primary Ciliary Dyskinesia )"
cp -R "$JOB_PATH/$EXAMPLEJOB" "$JOB_PATH/$EXAMPLENAME"
cd  "$JOB_PATH/$EXAMPLENAME"
# rename all the files

for f in ${EXAMPLEJOB}*.*; do 
    newname=${f/"$EXAMPLEJOB"/"$EXAMPLENAME"}
    mv "$f" "$newname"
done


# some files have job names and job file paths ... replace those with sed
sed_pattern="s/$EXAMPLEJOB/$EXAMPLENAME/g"
sed -i "$sed_pattern" "$EXAMPLENAME.json"
sed -i "$sed_pattern" job_info.json
sed -i "$sed_pattern" results.html
    

# make nicer jobs names in output files
sed -i 's/"JOBNAME": "example"/"JOBNAME": "$EXAMPLENAME"/g' "$EXAMPLENAME.json"
sed -i 's/"jobname": "example"/"jobname": "$EXAMPLENAME"/g' job_info.json 

linkname=${EXAMPLENAME//" "/"%20"}

