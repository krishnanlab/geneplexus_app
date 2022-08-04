# download_data_for_geneplexus.py
# the Geneplexus model requires extensive data to run.  If you use the package alone, 
# it automatically downloads the data that you need depending on model parameters.  

# This script uses a download method from the PyGenePlexus package to download all the files. 
# However this script  maintains a list of all files so that it is restartable and will not re-download
#
# NOTES
#   this does no quality checks on download files, so if file is only partially download you may have to delete it
#   python_dotenv package is not in the requirements file as the function app does not use it. 
#
# USAGE
#   using python3 from the shell
#   DATA_PATH=/path/where/you/want/stuff/to/go
#   python3 download_data_for_geneplexus.py

import os
from geneplexus.download import _download_file as geneplexus_download

def download_missing_files(file_list, data_dir ):
    """of the files in the file list, download only those files we don't have yet in data dir"""
    for filename in file_list:
        if os.path.exists(os.path.join(data_dir, filename)):
            print(f"already downloaded {filename}")
        else:
            print(f"downloading {filename}...")
            geneplexus_download(file =  filename, data_dir = data_dir)

all_files = [
    "CorrectionMatrixOrder_DisGeNet_BioGRID.txt",
    "CorrectionMatrixOrder_DisGeNet_GIANT-TN.txt",
    "CorrectionMatrixOrder_DisGeNet_STRING-EXP.txt",
    "CorrectionMatrixOrder_DisGeNet_STRING.txt",
    "CorrectionMatrixOrder_GO_BioGRID.txt",
    "CorrectionMatrixOrder_GO_GIANT-TN.txt",
    "CorrectionMatrixOrder_GO_STRING-EXP.txt",
    "CorrectionMatrixOrder_GO_STRING.txt",
    "CorrectionMatrix_DisGeNet_DisGeNet_BioGRID_Adjacency.npy",
    "CorrectionMatrix_DisGeNet_DisGeNet_BioGRID_Embedding.npy",
    "CorrectionMatrix_DisGeNet_DisGeNet_BioGRID_Influence.npy",
    "CorrectionMatrix_DisGeNet_DisGeNet_GIANT-TN_Adjacency.npy",
    "CorrectionMatrix_DisGeNet_DisGeNet_GIANT-TN_Embedding.npy",
    "CorrectionMatrix_DisGeNet_DisGeNet_GIANT-TN_Influence.npy",
    "CorrectionMatrix_DisGeNet_DisGeNet_STRING-EXP_Adjacency.npy",
    "CorrectionMatrix_DisGeNet_DisGeNet_STRING-EXP_Embedding.npy",
    "CorrectionMatrix_DisGeNet_DisGeNet_STRING-EXP_Influence.npy",
    "CorrectionMatrix_DisGeNet_DisGeNet_STRING_Adjacency.npy",
    "CorrectionMatrix_DisGeNet_DisGeNet_STRING_Embedding.npy",
    "CorrectionMatrix_DisGeNet_DisGeNet_STRING_Influence.npy",
    "CorrectionMatrix_DisGeNet_GO_BioGRID_Adjacency.npy",
    "CorrectionMatrix_DisGeNet_GO_BioGRID_Embedding.npy",
    "CorrectionMatrix_DisGeNet_GO_BioGRID_Influence.npy",
    "CorrectionMatrix_DisGeNet_GO_GIANT-TN_Adjacency.npy",
    "CorrectionMatrix_DisGeNet_GO_GIANT-TN_Embedding.npy",
    "CorrectionMatrix_DisGeNet_GO_GIANT-TN_Influence.npy",
    "CorrectionMatrix_DisGeNet_GO_STRING-EXP_Adjacency.npy",
    "CorrectionMatrix_DisGeNet_GO_STRING-EXP_Embedding.npy",
    "CorrectionMatrix_DisGeNet_GO_STRING-EXP_Influence.npy",
    "CorrectionMatrix_DisGeNet_GO_STRING_Adjacency.npy",
    "CorrectionMatrix_DisGeNet_GO_STRING_Embedding.npy",
    "CorrectionMatrix_DisGeNet_GO_STRING_Influence.npy",
    "CorrectionMatrix_GO_DisGeNet_BioGRID_Adjacency.npy",
    "CorrectionMatrix_GO_DisGeNet_BioGRID_Embedding.npy",
    "CorrectionMatrix_GO_DisGeNet_BioGRID_Influence.npy",
    "CorrectionMatrix_GO_DisGeNet_GIANT-TN_Adjacency.npy",
    "CorrectionMatrix_GO_DisGeNet_GIANT-TN_Embedding.npy",
    "CorrectionMatrix_GO_DisGeNet_GIANT-TN_Influence.npy",
    "CorrectionMatrix_GO_DisGeNet_STRING-EXP_Adjacency.npy",
    "CorrectionMatrix_GO_DisGeNet_STRING-EXP_Embedding.npy",
    "CorrectionMatrix_GO_DisGeNet_STRING-EXP_Influence.npy",
    "CorrectionMatrix_GO_DisGeNet_STRING_Adjacency.npy",
    "CorrectionMatrix_GO_DisGeNet_STRING_Embedding.npy",
    "CorrectionMatrix_GO_DisGeNet_STRING_Influence.npy",
    "CorrectionMatrix_GO_GO_BioGRID_Adjacency.npy",
    "CorrectionMatrix_GO_GO_BioGRID_Embedding.npy",
    "CorrectionMatrix_GO_GO_BioGRID_Influence.npy",
    "CorrectionMatrix_GO_GO_GIANT-TN_Adjacency.npy",
    "CorrectionMatrix_GO_GO_GIANT-TN_Embedding.npy",
    "CorrectionMatrix_GO_GO_GIANT-TN_Influence.npy",
    "CorrectionMatrix_GO_GO_STRING-EXP_Adjacency.npy",
    "CorrectionMatrix_GO_GO_STRING-EXP_Embedding.npy",
    "CorrectionMatrix_GO_GO_STRING-EXP_Influence.npy",
    "CorrectionMatrix_GO_GO_STRING_Adjacency.npy",
    "CorrectionMatrix_GO_GO_STRING_Embedding.npy",
    "CorrectionMatrix_GO_GO_STRING_Influence.npy",
    "Data_Adjacency_BioGRID.npy",
    "Data_Adjacency_GIANT-TN.npy",
    "Data_Adjacency_STRING-EXP.npy",
    "Data_Adjacency_STRING.npy",
    "Data_Embedding_BioGRID.npy",
    "Data_Embedding_GIANT-TN.npy",
    "Data_Embedding_STRING-EXP.npy",
    "Data_Embedding_STRING.npy",
    "Data_Influence_BioGRID.npy",
    "Data_Influence_GIANT-TN.npy",
    "Data_Influence_STRING-EXP.npy",
    "Data_Influence_STRING.npy",
    "Edgelist_BioGRID.edg",
    "Edgelist_GIANT-TN.edg",
    "Edgelist_STRING-EXP.edg",
    "Edgelist_STRING.edg",
    "GSCOriginal_DisGeNet.json",
    "GSCOriginal_GO.json",
    "GSC_DisGeNet_BioGRID_GoodSets.json",
    "GSC_DisGeNet_BioGRID_universe.txt",
    "GSC_DisGeNet_GIANT-TN_GoodSets.json",
    "GSC_DisGeNet_GIANT-TN_universe.txt",
    "GSC_DisGeNet_STRING-EXP_GoodSets.json",
    "GSC_DisGeNet_STRING-EXP_universe.txt",
    "GSC_DisGeNet_STRING_GoodSets.json",
    "GSC_DisGeNet_STRING_universe.txt",
    "GSC_GO_BioGRID_GoodSets.json",
    "GSC_GO_BioGRID_universe.txt",
    "GSC_GO_GIANT-TN_GoodSets.json",
    "GSC_GO_GIANT-TN_universe.txt",
    "GSC_GO_STRING-EXP_GoodSets.json",
    "GSC_GO_STRING-EXP_universe.txt",
    "GSC_GO_STRING_GoodSets.json",
    "GSC_GO_STRING_universe.txt",
    "IDconversion_Homo-sapiens_ENSG-to-Entrez.json",
    "IDconversion_Homo-sapiens_ENSP-to-Entrez.json",
    "IDconversion_Homo-sapiens_ENST-to-Entrez.json",
    "IDconversion_Homo-sapiens_Entrez-to-ENSG.json",
    "IDconversion_Homo-sapiens_Entrez-to-Name.json",
    "IDconversion_Homo-sapiens_Entrez-to-Symbol.json",
    "IDconversion_Homo-sapiens_Symbol-to-Entrez.json",
    "NodeOrder_BioGRID.txt",
    "NodeOrder_GIANT-TN.txt",
    "NodeOrder_STRING-EXP.txt",
    "NodeOrder_STRING.txt",
    "PreTrainedWeights_DisGeNet_BioGRID_Adjacency.json",
    "PreTrainedWeights_DisGeNet_BioGRID_Embedding.json",
    "PreTrainedWeights_DisGeNet_BioGRID_Influence.json",
    "PreTrainedWeights_DisGeNet_GIANT-TN_Adjacency.json",
    "PreTrainedWeights_DisGeNet_GIANT-TN_Embedding.json",
    "PreTrainedWeights_DisGeNet_GIANT-TN_Influence.json",
    "PreTrainedWeights_DisGeNet_STRING-EXP_Adjacency.json",
    "PreTrainedWeights_DisGeNet_STRING-EXP_Embedding.json",
    "PreTrainedWeights_DisGeNet_STRING-EXP_Influence.json",
    "PreTrainedWeights_DisGeNet_STRING_Adjacency.json",
    "PreTrainedWeights_DisGeNet_STRING_Embedding.json",
    "PreTrainedWeights_DisGeNet_STRING_Influence.json",
    "PreTrainedWeights_GO_BioGRID_Adjacency.json",
    "PreTrainedWeights_GO_BioGRID_Embedding.json",
    "PreTrainedWeights_GO_BioGRID_Influence.json",
    "PreTrainedWeights_GO_GIANT-TN_Adjacency.json",
    "PreTrainedWeights_GO_GIANT-TN_Embedding.json",
    "PreTrainedWeights_GO_GIANT-TN_Influence.json",
    "PreTrainedWeights_GO_STRING-EXP_Adjacency.json",
    "PreTrainedWeights_GO_STRING-EXP_Embedding.json",
    "PreTrainedWeights_GO_STRING-EXP_Influence.json",
    "PreTrainedWeights_GO_STRING_Adjacency.json",
    "PreTrainedWeights_GO_STRING_Embedding.json",
    "PreTrainedWeights_GO_STRING_Influence.json"
]
    

if __name__ == "__main__":
    data_dir = os.getenv('DATA_PATH', default='../data')

    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    download_missing_files(all_files, data_dir)


