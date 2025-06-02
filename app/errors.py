"""
Copyright (c) 2023 TU Delft 3D geoinformation group, Ravi Peters (3DGI), and Balázs Dukai (3DGI)
"""

import json
import logging

from flask import jsonify

from werkzeug.exceptions import HTTPException

from app import app, auth


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


@app.errorhandler(404)
def resource_not_found(e):
    e.description = (
        "The requested resource (or feature) does not exist on the server. "
        "For example, a path parameter had an incorrect value."
    )
    return jsonify(
        code=e.code,
        name=e.name,
        description=e.description
    ), 404


@auth.error_handler
def auth_error(status):
    if status == 401:
        error = dict(
            code=status,
            name="Unauthorized",
            description=(
                "The request requires user authentication. The response "
                "includes a WWW-Authenticate header field containing a "
                "challenge applicable to the requested resource."
            )
        )
    elif status == 403:
        error = dict(
            code=status,
            name="Forbidden",
            description=(
                "The server understood the request, but is refusing to fulfil "
                "it. Status code 403 indicates that authentication is not the "
                "issue, but the client is not authorized to perform the "
                "requested operation on the resource."
            )
        )
    else:
        logging.error(
            "Flask-HTTPAuth error_handler is handling an error "
            "that is not 401 or 403.")
        error = dict(
            code=500,
            name="Internal Server Error",
            description=(
                "The server encountered an internal error and was unable to"
                " complete your request. Either the server is overloaded or"
                " there is an error in the application."
            )
        )
    return jsonify(error), status
