import csv
import os
import shutil

from sqlalchemy import MetaData, Table, text

from .connection import db
from .models import Comparison, CustomItemPair, Group, Item, ItemGroup, UserGroup, UserItem


class Exporter:
    """Export Flask website database."""

    def __init__(self, app) -> None:
        """Initialise the export with the flask app and the required models."""
        self.app = app
        self.models = [Group, Item, ItemGroup, UserGroup, Comparison, CustomItemPair, UserItem]

    def get_outcome_data(self):
        """Get the data for the outcome table in the form of a list of dictionaries.

        If the comparison was skipped it is ignored.
        If item 1 was selected then the outcome is 0.
        If item 2 was selected then the outcome is 1.
        If the comparison was tied then the outcome is 2.
        """
        data_list = []
        data = Comparison.query.all()
        for item in data:
            if item.state != 'skipped':
                entry = {
                    'item_1_id': item.item_1_id,
                    'item_2_id': item.item_2_id,
                }
                if item.state == 'tied':
                    entry['outcome'] = 2
                elif item.selected_item_id == item.item_1_id:
                    entry['outcome'] = 0
                elif item.selected_item_id == item.item_2_id:
                    entry['outcome'] = 1
                data_list.append(entry)
        return data_list

    def save(self, location, file_type):
        """Export the database tables to a zip file of either csv or tsv files."""
        output_directory = os.path.join(location, 'database_tables')
        zip_path = os.path.join(location, 'database_export')
        if file_type == 'tsv':
            delimiter = '\t'
        else:
            delimiter = ','

        # make a temp directory in the location which we will later zip
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # delete the zip file if it exists
        if os.path.exists(f'{zip_path}.zip'):
            os.remove(f'{zip_path}.zip')

        # export the models
        for m in self.models:
            data = m.query.all()
            data_list = [item.as_dict() for item in data]
            if len(data_list) > 0:
                keys = data_list[0].keys()
                with open(
                    os.path.join(output_directory, f'{m.__tablename__}.{file_type}'), mode='w', encoding='utf-8'
                ) as csv_out:
                    csv_writer = csv.DictWriter(csv_out, keys, delimiter=delimiter)
                    csv_writer.writeheader()
                    csv_writer.writerows(data_list)

        # The user model needs to be accessed manually due the dynamic fields
        db_engine = db.engines[None]
        db_meta = MetaData()
        db_meta.reflect(bind=db_engine)
        table = Table('user', db_meta)
        columns = table.columns.keys()
        sql = text("select {} from user;".format(', '.join(columns)))
        with db.engine.begin() as connection:
            results = connection.execute(sql)
        with open(os.path.join(output_directory, f'user.{file_type}'), mode='w', encoding='utf-8') as csv_out:
            writer = csv.writer(csv_out, delimiter=delimiter)
            writer.writerow(columns)
            for record in results:
                writer.writerow(record)

        # make a new table from the data used for BSBT analysis
        table = Table('outcome', db_meta)
        data_list = self.get_outcome_data()
        if len(data_list) > 0:
            keys = data_list[0].keys()
            with open(os.path.join(output_directory, f'outcome.{file_type}'), mode='w', encoding='utf-8') as csv_out:
                csv_writer = csv.DictWriter(csv_out, keys, delimiter=delimiter)
                csv_writer.writeheader()
                csv_writer.writerows(data_list)

        # zip the folder
        shutil.make_archive(zip_path, 'zip', location)

        # remove the temp directory
        shutil.rmtree(os.path.join(location, 'database_tables'))
