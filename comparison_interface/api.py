import csv
from functools import wraps
from io import BytesIO, StringIO

from cachetools.func import ttl_cache
from flask import Blueprint, abort, current_app, request, send_file, session

from .db.export import Exporter
from .db.models import Comparison, Item
from .views.request import Request

blueprint = Blueprint('api', __name__)


@ttl_cache()
def _get_key_from_file():
    try:
        api_key_file = current_app.config['API_KEY_FILE']
    except KeyError:
        api_key_file = '.apikey'
    try:
        with open(api_key_file, mode='r') as keyfile:
            api_key = keyfile.read().replace('\n', '')
    except FileNotFoundError:
        # then the server is not configured correctly as no api key has been provided
        raise
    return api_key


def require_api_key(function):
    """Wrapper to ensure we have the correct key in the header to allow access to the api."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            api_key = _get_key_from_file()
        except FileNotFoundError:
            # then the server is not configured correctly as no api key has been provided
            abort(501)
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == api_key:
            return function(*args, **kwargs)
        else:
            # then the request does not have permission to access the api
            abort(401)

    return wrapper


class Judgements(Request):
    """API to get judgements."""

    def get(self, _):
        """Get all of the comparisons in the database and return them in csv format as text."""
        data = Comparison.query.all()
        with StringIO() as file_buffer:
            data_list = [item.as_dict() for item in data]
            if len(data_list) > 0:
                keys = data_list[0].keys()
                csv_writer = csv.DictWriter(file_buffer, keys)
                csv_writer.writeheader()
                csv_writer.writerows(data_list)
            file_buffer.seek(0)
            return send_file(BytesIO(file_buffer.read().encode('utf-8')), as_attachment=False, mimetype='text')


class Outcomes(Request):
    """API to get outcomes."""

    def get(self, _):
        """Calculate the outcomes and return them in csv format as text."""
        data_list = Exporter(current_app).get_outcome_data()
        with StringIO() as file_buffer:
            if len(data_list) > 0:
                keys = data_list[0].keys()
                csv_writer = csv.DictWriter(file_buffer, keys)
                csv_writer.writeheader()
                csv_writer.writerows(data_list)
            file_buffer.seek(0)
            return send_file(BytesIO(file_buffer.read().encode('utf-8')), as_attachment=False, mimetype='text')


class Items(Request):
    """API to get the items (images)."""

    def get(self, _):
        """Get all of items in the database and return them in csv format as text."""
        data = Item.query.all()
        with StringIO() as file_buffer:
            data_list = [item.as_dict() for item in data]
            if len(data_list) > 0:
                keys = data_list[0].keys()
                csv_writer = csv.DictWriter(file_buffer, keys)
                csv_writer.writeheader()
                csv_writer.writerows(data_list)
            file_buffer.seek(0)
            return send_file(BytesIO(file_buffer.read().encode('utf-8')), as_attachment=False, mimetype='text')


@blueprint.route('/api/judgements', methods=['GET'])
@require_api_key
def api_judgements():
    """Handle api URL to get judgements made."""
    return Request.process(Judgements(current_app, session), request)


@blueprint.route('/api/outcomes', methods=['GET'])
@require_api_key
def api_outcomes():
    """Handle api URL to get outcomes."""
    return Request.process(Outcomes(current_app, session), request)


@blueprint.route('/api/items', methods=['GET'])
@require_api_key
def api_items():
    """Handle api URL to get the items table (for mapping with item ids in judgements table)."""
    return Request.process(Items(current_app, session), request)
