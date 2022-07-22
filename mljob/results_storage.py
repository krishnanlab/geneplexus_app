""" this class is to save and read from output from  GenePlexus package for use in an application
This is a step towards different storage methods beyond posix file storage (e.g. cloud storage)
usage:
    usage
        results_store = ResultsFiler(job_path = config['JOB_PATH'])
        job_output = geneplexus_runner(params)
        results_store.save_output(job_name, job_output)

"""

import os, sys
import json
import pandas as pd


class ResultsFileStore():
    """posix file-based model output reader/writer"""

    def __init__(self,job_path = "./jobs"):
        self.job_path

    def results_folder(self, job_name):
        os.path.join(self.job_path, job_name)

    def results_folder_exists(self,job_name):
        """is there a job folder already? 
        input : job_name valid name of a job
        output : T/F
        """
        return ( os.path.exists(self.results_folder(job_name))   )

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
        results_file = self.save_txt_results(output_path, job_name, 'results.txt', results_file_content )
        
        # the 'graph' is a dict of dicts (node, edges), so save in different format
        graph_file = self.save_graph_results(output_path, job_name, graph)

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

        
        job_info_path = self.construct_results_filepath(job_name, 'job_info', ext = 'json')
        print(f"saving job info to {job_info_path} ",file=sys.stderr)   
        with open(job_info_path, 'w') as jf:
            json.dump(job_info, jf)

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
        """ consistently create output file name from path and job name"""
        if( ext and ext[0] != '.'):
            ext = '.' + ext

        output_file = job_name + '_' +  output_name +  ext
        return(output_file)

    def construct_results_filepath(self, job_name, output_name, ext = ''):
        """ consistently create output file name from path and job name"""
        if( ext and ext[0] != '.'):
            ext = '.' + ext

        output_path = self.results_folder(job_name)

        output_file_path = os.path.join(output_path, output_name +  ext)
        return(output_file_path)

    #============== file save functions by format

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
            output_df = pd.read_csv(output_filepath, sep = '\t')
            return(output_df)
        else:
            print(f"output file not found: {output_filepath} ",file=sys.stderr)
            return(None)
        
    def read_job_info(self, job_name):
        """ read in the job information dictionary"""
        
        job_info_path = self.construct_results_filepath(job_name, 'job_info', ext = 'json')
        if os.path.exists(job_info_path):
            with open(job_info_path) as f:
                job_info = json.load(f)

            return(job_info)
        else:
            print(f"job info file not found: {job_info_path} ",file=sys.stderr)
            return(None)




