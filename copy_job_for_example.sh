#!/usr/bin/env bash

# this will take an existing job and put it as the example 
# this assumes the env var $JOB_PATH is set ( use source .env to set it )
# TODO check for parameter

export EXAMPLEJOB=$1
export EXAMPLENAME="example"  #  ( Primary Ciliary Dyskinesia )"
cp -R "$JOB_PATH/$EXAMPLEJOB" "$JOB_PATH/$EXAMPLENAME"
cd  "$JOB_PATH/$EXAMPLENAME"
# rename all the files

for f in ${EXAMPLEJOB}*.*; do 
    newname=${f/"$EXAMPLEJOB"/"$EXAMPLENAME"}
    mv "$f" "$newname"
done

# for this special example job, changing the name that's displayed from the name (folder) of the job
# normally they are the same
# this is to have a complex name displayed for the example page, but keep the URL simple to just /example
export DISPLAYNAME="example ( Primary Ciliary Dyskinesia )"

# some files have job names and job file paths ... replace those with sed
sed_pattern="s/$EXAMPLEJOB/$DISPLAYNAME/g"
sed -i "$sed_pattern" "$EXAMPLENAME.json"
sed -i "$sed_pattern" job_info.json
sed -i "$sed_pattern" results.html
    

# make nicer jobs names in output files
sed -i 's/"JOBNAME": "example"/"JOBNAME": "$DISPLAYNAME"/g' "$EXAMPLENAME.json"
sed -i 's/"jobname": "example"/"jobname": "$DISPLAYNAME"/g' job_info.json 

linkname=${EXAMPLENAME//" "/"%20"}

