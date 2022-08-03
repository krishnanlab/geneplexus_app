""" this class is to save and read from output from  GenePlexus package for use in an application
This is a step towards different storage methods beyond posix file storage (e.g. cloud storage)
usage:
    # save
    job_config = {jobname:'whatever', etc}
    results_store = ResultsFileStore(job_path = config['JOB_PATH'])
    
    if results_store.create(job_name):
        path_to_input_file = results_store.save_input_file(job_name, geneset)
        job_output = run_geneplexus.run_and_save(job_config, path_to_input_file)  # how to emit status?
        results_store.save_output(job_name, job_output)
    else:
        # exception

    ### wait for job to complete
    if results_store.results_folder_exists(job_name) and results_store.read_status(job_name) == "Completed":
        results = results_store.read(job_name)
        
"""



import os, sys, shlex
from  shutil import rmtree
from slugify import slugify
import json
from pandas import read_csv
import logging


class ResultsFileStore():
    """posix file-based model output reader/writer"""

    def __init__(self,job_path, logger_name = None):
        """"""
        if job_path and os.path.exists(job_path):
            self.job_path = job_path
            self.logger = logging.getLogger(logger_name)
        else:
            raise Exception(f"error job path doesn't exist {job_path}")
        
        self.status_filename = "jobstatus"

    
    def path_friendly_job_name(self,job_name):
        """modify job name to be used as folder names for file storage, if necessary"""
        if not job_name:
            return ""
        else:
            return slugify(job_name.lower())

    def results_folder(self, job_name):
        """ return standardized path name used to store jobs"""
        
        if job_name:
            # can't handle spaces etc. so make it work before joining
            job_name = self.path_friendly_job_name(job_name)
            return os.path.join(self.job_path, job_name)
        else: 
            self.logger.error('no job name given')
            return ""

    def exists(self,job_name):
        """ convenience shortcut for results_folder_exists"""
        return(self.results_folder_exists(job_name))
    
    def results_folder_exists(self,job_name):
        """is there a job folder already? 
        input : job_name valid name of a job
        output : T/F
        """

        rf =  self.results_folder(job_name)
        if rf:
            return ( os.path.exists(rf)   )
        else:
            return False

    def has_input_file(self,job_name, input_file_name = "geneset"):
        """check that an input file with standard name exists in store"""
        full_input_file_name = self.standard_input_file_name(job_name, input_file_name)
        input_file_path = self.construct_results_filepath(job_name, full_input_file_name)
        return(os.path.exists(input_file_path))

    def results_file_location(self, job_name, file_name):
        """ return full path for location files by name (e.g add the path to it)"""
        rf = self.results_folder(job_name)
        full_file_path = os.path.join(rf, file_name)
        return(full_file_path)

    def results_has_file(self,job_name, file_name):
        """ check if a specific file is in the store for that job name"""
        return(os.path.exists( self.results_file_location(job_name, file_name)))

    def create(self, job_name):
        """ this will create new folder, but catches exceptions and returns None if there is an issue
        input : valid job_name
        output : same object for object chaining, if error return None"""
        if not job_name:
            self.logger.error("no job name given, can't create results store")
            return False
        
        if self.results_folder_exists(job_name):
            self.logger.error("results folder already exist, not overwriting")
            return True

        new_path = self.results_folder(job_name)
        
        try:
            os.mkdir( new_path )
            return(True)

        except Exception as e:
            self.logger.error(e)
            return False

    def delete(self, job_name, confirmation = False):
        """ delete a file storage (folder) for this jobname.
        inputs: 
        job_name : path friendly job name, str
        confirmation  : T/F simple additional param to reduce unintended deletions"""
        if not confirmation:
            return False

        if self.results_folder_exists(self,job_name):
            try:
                rmtree(self.self.results_folder(job_name))
                return True
            except Exception as e: 
                self.logger.error(f"exception when attempting delete {e}")
                return False
        else:
            self.logger.error(f"folder for {job_name} not found, can't delete")
            return False

    def save_output(self,job_name, job_output):
        """ convenience function to use dictionary for args"""
        net_type = job_output.get('net_type')
        features = job_output.get('features')
        GSC = job_output.get('GSC')
        avgps = job_output.get('avgps')
        input_count = job_output.get('input_count')
        positive_genes = job_output.get('positive_genes')
        df_probs = job_output.get('df_probs')
        df_sim_go = job_output.get('df_sim_go')
        df_sim_dis = job_output.get('df_sim_dis')
        df_convert_out = job_output.get('df_convert_out')
        graph = job_output.get('graph')
        df_edgelist = job_output.get('df_edgelist')

        job_info = self.save(job_name, net_type, features, GSC, avgps, input_count, 
            positive_genes, 
            df_probs, 
            df_sim_go, 
            df_sim_dis, 
            df_convert_out, 
            graph, 
            df_edgelist)

    def save(self, job_name, net_type, features, GSC, avgps, input_count, positive_genes, 
        df_probs, df_GO, df_dis, df_convert_out_subset, graph, df_edgelist):
        """ save each of the model results to a file based on type"""

        output_path = self.results_folder(job_name)

        # data frames
        df_probs_file = self.save_df_results(job_name, 'df_probs', df_probs)
        df_GO_file = self.save_df_results(job_name, 'df_GO',df_GO )
        df_convert_out_subset_file = self.save_df_results(job_name, 'df_convert_out_subset', df_convert_out_subset)
        df_dis_file = self.save_df_results(job_name, 'df_dis',df_dis)
        df_edgelist_file = self.save_df_results(job_name, 'df_edgelist', df_edgelist )

        # placeholder : this was the HTML representation of the results visualization, no longer used but required in older code
        results_file_content = f"<html><body><p>{job_name}</p></html>"
        results_file = self.save_txt_results(job_name, 'results.txt', results_file_content )

        # the 'graph' is a dict of dicts (node, edges), so save in different format
        graph_file = self.save_graph_results(job_name, graph)

        # copy the results file names into this dictionary (without path) 
        job_info = {
            'job_name': job_name,
            'net_type': net_type,
            'features': features,
            'GSC': GSC,
            'avgps': avgps, 
            'input_count': input_count, 
            'positive_genes': positive_genes,
            'df_probs_file': df_probs_file, 
            'df_GO_file': df_GO_file, 
            'df_dis_file': df_dis_file, 
            'df_convert_out_subset_file': df_convert_out_subset_file, 
            'graph_file':  graph_file,
            'df_edgelist_file' : df_edgelist_file
            }

        
        self.save_json_results(job_name, 'job_info', job_info)
        
        return(job_info)

    def read(self,job_name):
        """opposite of writing output, read all output from a job and load into memory """

        #TODO this may be redundant with methods in jobs.py so reconcile these two modules
        job_info = self.read_job_info(job_name)

        if job_info:
            # add new elements to this dictionary to return all data frames in a single dictionary
            # TODO try/catch around these to catch I/O exceptions
            # TODO check if any of these return None and raise an exception if it does
            data_frame_list = ['df_probs','df_GO','df_convert_out_subset','df_dis','df_edgelist']
            for dfname in data_frame_list:
                job_info[dfname] = self.read_df_results(job_name, dfname)
        
            job_info['graph'] = self.read_graph_results(job_name)
        
        # returns None or empty if no job info was found
        return(job_info)

    #============== consistent file names and paths

    def construct_results_filename(self, job_name, output_name, ext = ''):
        """ consistently create output file name from file type/name and job name"""
        if( ext and ext[0] != '.'):
            ext = '.' + ext

        output_file = job_name + '_' +  output_name +  ext
        return(output_file)

    def construct_results_filepath(self, job_name, output_name):
        """ consistently create output file name from path and job name"""

        output_path = self.results_folder(job_name)

        output_file_path = os.path.join(output_path, output_name)
        return(output_file_path)

    def standard_input_file_name(self,job_name, input_file_name = "geneset"):
        """ standardized input file name for this storage system"""
        return self.construct_results_filename(job_name, input_file_name, 'txt' )

    #============== WRITE
    
    def save_txt_results(self, job_name, output_name, output_content):
        """ save any data from job, output name must have the extension"""
        output_filename = self.construct_results_filename(job_name, output_name)
        output_filepath = self.construct_results_filepath(job_name, output_filename)
        try:
            with open(output_filepath, 'w') as outfile:
                outfile.writelines(output_content)
            return(output_filename)
        except Exception as e:
            return("")     


    def save_json_results(self, job_name, output_name, data):
        json_results_filename = self.construct_results_filename(job_name, output_name,ext = 'json')
        json_file_path = self.construct_results_filepath(job_name, json_results_filename)
        self.logger.info(f"saving job info to {json_file_path} ")   
        with open(json_file_path, 'w') as jf:
            json.dump(data, jf)

        return(json_file_path)


    def save_df_results(self, job_name, output_name, output_df):
        """ save data frames from model runs in a consistent way"""
        output_filename = self.construct_results_filename(job_name, output_name, '.tsv')
        output_filepath = self.construct_results_filepath(job_name, output_filename)
        output_df.to_csv(path_or_buf = output_filepath, sep = '\t', index = False, line_terminator = '\n')
        return(output_filename)

    def save_graph_results(self, job_name, graph):
        """save the data that makes up the network graph to output folder, in JSON format.  
        the 'graph' is a dict of dicts (node, edges), so just save as json"""
        graph_file = self.construct_results_filename(job_name, 'graph', 'json')
        graph_file_path = self.construct_results_filepath(job_name, graph_file)
        with open(graph_file_path, 'w') as gf:
            json.dump(graph, gf)

        return(graph_file)
    
        
    def save_input_file(self, job_name, data, input_file_name = "geneset"):
        """ save input file in standardized way.  
        parameters: 
            job_name
            data : data to write
            input_file_name : core part of file, no extension. optional can override the default () but shouldn't for consistency)
        outputs:
            if file written correctly, the name of the input file created
            if there is an error during writing, an empty string
        """ 
        
        full_input_file_name = self.standard_input_file_name(job_name, input_file_name)
        input_file_path = self.construct_results_filepath(job_name, full_input_file_name)
        try:
            with open(input_file_path, 'w') as f:
                f.write('\n'.join(data))

            return(full_input_file_name)
        except Exception as e:
            self.logger.error(f"can't save file {input_file_path} : {e}")
            return("")     

    def save_status(self, job_name, msg):
        """standardized api for saving/reading status from file store"""
        status_file_name = self.save_txt_results(job_name, self.status_filename, msg)
        return(status_file_name)

    ############ READ

    def read_status(self, job_name):
        status = self.read_txt_results(job_name, self.status_filename)
        return(status)


    def read_input_file(self, job_name, input_file_name = "geneset"):    
        """ read the geneset file with standardized filename, path, and file extension
        parameters:
            job_name : name of the job that this was stored in
            input_file_name : optional base name of the file (with no extension)
        outputs:
            contents of the input file as a list of data, or an empty list if there is a problem reading the file
        """
        
        full_input_file_name = self.standard_input_file_name(job_name, input_file_name)
        input_file_path = self.construct_results_filepath(job_name, full_input_file_name)
        try:
            with open(input_file_path, 'r') as f:
                # using shlex here allows for more flexible storage formats,
                # e.g. storing quoted ('abc'\n'def'\n) or not quoted
                data =  shlex.split(f.read())
        except Exception as e:
            self.logger.error(f"could not read input file {input_file_path} : {e}")
            data = []

        return(data)

    def read_config(self, job_name):
        """ read the standard configuration file stored when the job is created 
        return empty dict if not found"""
        output_name = "job_config.json"
        job_config_json = self.read_txt_results(self, job_name, output_name )

        if job_config_json:
            job_config = json.loads(job_config_json)
        else:
            job_config = {}

        return(job_config)



    def read_txt_results(self, job_name, output_name ):
        """ read generic text file, output name must have the extension"""

        output_filename = self.construct_results_filename(job_name, output_name)
        output_filepath = self.construct_results_filepath(job_name, output_filename)
        try:
            with open(output_filepath, 'r') as outfile:
                output_content = outfile.read()
            return(output_content)
        except Exception as e:
            logging.error(f"can't read from {output_filename} : {e}")
            return("")     


    def read_graph_results(self, job_name):
        """ read in a graph as saved by output methoda above"""
        graph_file = self.construct_results_filename(job_name, 'graph', 'json')
        graph_file_path = self.construct_results_filepath(job_name, graph_file)
        with open(graph_file_path, 'r') as gf:
            graph_data = json.load(gf)

        return(graph_data)

    def read_df_results(self, job_name, output_name):
        """retrieve individual data frames from output folder given the name of the file, assuming they are saved as tsv
        returns: pandas data frame or None if not found
        """
        output_filename = self.construct_results_filename(job_name, output_name, '.tsv')
        output_filepath = self.construct_results_filepath(job_name, output_filename)
        
        if os.path.exists(output_filepath):
            # TODO try /catch
            output_df = read_csv(output_filepath, sep = '\t')
            return(output_df)
        else:
            self.logger.error(f"output file not found: {output_filepath} ")
            return(None)
        
    def read_job_info(self, job_name):
        """ read in the job information dictionary"""
        job_info_filename = self.construct_results_filename(job_name, 'job_info', ext = 'json')
        job_info_path = self.construct_results_filepath(job_name,  job_info_filename)
        if os.path.exists(job_info_path):
            with open(job_info_path) as f:
                job_info = json.load(f)

            return(job_info)
        else:
            self.logger.error(f"job info file not found: {job_info_path} ")
            return(None)


"""

Example Usage:    

import pytest, os
from mljob.job_manager import generate_job_id
from mljob.results_storage import ResultsFileStore


from dotenv  import load_dotenv; load_dotenv()
job_path = os.getenv('JOB_PATH')
results_store = ResultsFileStore(job_path)
type(results_store)


job_name = generate_job_id()
rs = results_store.create(job_name)
print(results_store.results_folder_exists(job_name))
type(rs)

with open('tests/example_gene_file.txt') as f:
    genes = f.read()

fname = results_store.save_txt_results(job_name, 'inputfile.txt', genes)
expected_name = results_store.construct_results_filename(job_name, 'inputfile.txt')
fname == expected_name
results_store.results_has_file(job_name, expected_name) # true
results_store.delete(job_name)

"""