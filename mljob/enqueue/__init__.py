""" queuejob function :  add data to queue to trigger runjob function
"""

#triggerprocessing: take input from http and enqueue items in a list, triggering the processing of those items
# TODO: rename to enqueue_job since it does't trigger anything, it just puts it on the queue.  
# TODO: in body of function, check that the job can be run in the first place
#  import job_manager.  job_manager.exists(jobid)
# TODO: some protection from running this function.e.g  shared secret with app apikey
# 
import logging
import azure.functions as func

def main(req: func.HttpRequest, msg: func.Out[func.QueueMessage]) -> func.HttpResponse:
    """queue processing version, gets a list of documents to process"""
    
    logging.info('job enqueue triggered.')

    # jobnames param is a either a single element or an array msg.set(["Element1", "Element2", ...])
    try:
        req_body = req.get_json()
        jobnames = req_body.get('jobnames')
    except ValueError:
        logging.info('job request incomplete (missing jobnames')

        return func.HttpResponse(
             "Please pass a list of jobids as a parameter in the request body",
             status_code=400
        )
    
    if jobnames:

        logging.info(f"enqueuing {jobnames}.")
        
        # TODO return 202 not 200 and see if that works. 

        try:
            # this adds jobis to the az storage queue.  If 'jobids' is an array, automatically parses
            msg.set(jobnames)
            logging.info(f"msg queued {jobnames}.")
             
            return func.HttpResponse(
                "processing job(s) " + str(jobnames),
                status_code=200
            )

        except Exception as e:
            logging.info(f"error when enqueuing jobids {jobnames}.")
            return func.HttpResponse(
                f"Error: {e}",
                status_code=500
            )
