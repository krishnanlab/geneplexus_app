# gpcontainers.sh
# manage container instances
# usage:  
# 1. az login 
# 2. set sub with az account set --name "subname"
# 4. source gpcontainers.sh
# 5. az_delete_completed_acis "resource group name"

az_count_acis ()
{
    readonly AZRG=${1:?"The resource group must be specified."}
    echo "number container groups in resource group $AZRG:"
    az container list -g $AZRG --query "[].name" -o tsv | wc -l
}

az_delete_completed_acis ()
{
    #### ZSH!!
    readonly AZRG=${1:?"The resource group must be specified."}

    # this deletes all container groups in the current resource group that have completed
    echo "deleting all CIs in $AZRG"

    for n in `az container list -g $AZRG  --query "[].name" -o tsv`; do
        # get status of first container (only one container for these ACI groups)
        ACISTATE=`az container show -g $AZRG --name $n --query "containers[0].instanceView.currentState.detailStatus"`
        if [[ "$ACISTATE" == "\"Completed\"" ]]; then
            echo "deleting ACI $n"
            az container delete -g $AZRG --name $n -y
        fi
    done
}


echo "current az subscription set to" 
az account show --query 'name'
echo "--- all subs"
az account list --query '[].name'
echo "---- change this with az account set --name 'name'"
echo "the two functions here are:"
echo  "az_count_acis <rg> "
echo "az_delete_completed_acis <rg>"


