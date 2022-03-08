# The GenePlexus Web Application

### Introduction 

GenePlexus ( https://geneplexus.net ) is a web application and job-running system that allows a researcher to utilize a powerful, network-based machine learning method to gain insights into their gene set of interest and additional functionally similar genes.  Once a user uploads their own set of genes and chooses between a number of different network representations, GenePlexus provides predictions of how associated every gene in the network is to the input set. The web-server also provides interpretability through network visualization and comparison to other machine learning models trained on thousands of known pathway and disease gene sets.

This repository contains the code used to implement the web application including code for:

 - Developing the python flask application
 - Creating the cloud infrastructure on Microsoft Azure
 - Training the model and generate the results
 - Creating Docker containers to deploy on the cloud

The GenePlexus method has been extensively benchmarked in the Bioinformatics article titled Supervised learning is an accurate method for network-based gene classification. The code-base used to reproduce the results in that manuscript are found at https://github.com/krishnanlab/GenePlexus.

For more information or help contact us at help[at]geneplexus.net
