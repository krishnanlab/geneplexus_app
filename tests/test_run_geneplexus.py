""" test run_geneplexus module, using file-based results store, 
requires .env and data to be available on DATA_PATH config var 
"""
import pytest, os, shlex

from mljob.run_geneplexus import run_and_save

from mljob.results_storage import ResultsFileStore
from mljob.job_manager import generate_job_id
import logging


def test_true(job_name):
    assert job_name is not None

def test_run_geneplexus(job_name, results_store, data_path):
    """ minimum test run of GP.  takes time to complete"""

    rs_created = results_store.create(job_name)
    if not rs_created:
    # rs_created = results_store.create(job_name)
    # if not rs_created or results_store.exists(job_name):
        pytest.fail("couldn't create results store")
        
    with open('tests/example_gene_file.txt') as f:
        genes = shlex.split(f.read())

    input_file_name = results_store.save_input_file(job_name, genes)
    
    print(f"running job {job_name}")
    
    # test run typical options ( and not too long of a test)
    net_type='BioGRID'
    features='Embedding'
    GSC='GO' 

    try:
        job_ran = run_and_save(job_name, results_store, data_path, logging = logging, 
            net_type=net_type, features=features, GSC=GSC )
    except Exception as e:
        pass

    assert job_ran == True, "job runner returned false"

    assert results_store.results_has_file(job_name, file_name = input_file_name) == True

    
    # check if files expected are present
    graph_file_name = results_store.construct_results_filename(job_name, "graph", 'json')
    assert results_store.results_has_file(job_name, file_name = graph_file_name ) == True
    
    expected_filenames = [
        results_store.construct_results_filename(job_name, "graph", 'json'),
        results_store.construct_results_filename(job_name, "df_GO", ext="tsv"),
        results_store.construct_results_filename(job_name, "df_edgelist", ext="tsv"),
        results_store.construct_results_filename(job_name, "df_convert_out_subset", ext="tsv"),
        results_store.construct_results_filename(job_name, "df_probs", ext="tsv"),
        results_store.construct_results_filename(job_name, "job_info", ext="json"),
        results_store.construct_results_filename(job_name, "df_dis", ext="tsv"),
        results_store.construct_results_filename(job_name, "geneset", ext="txt"),
        results_store.construct_results_filename(job_name, "results", ext="txt")
        ]

    for file_name in expected_filenames:
        assert results_store.results_has_file(job_name, file_name = file_name )

