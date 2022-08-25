import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    msg = "test azure function working. " 
    if name:
        return func.HttpResponse(f"{msg} name = {name}")
    else:
        return func.HttpResponse( f"{msg} missing parameter 'name'",status_code=200)
