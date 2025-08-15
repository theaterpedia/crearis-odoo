from odoo.fields import Field
import psycopg2
import json

# this is nonfunctional / experimental
# we combine this: https://gist.github.com/danmana/5242f37b7d63daf4698de7c61c8b59fc
# and this: https://github.com/mkumar-02/odoo-json-field/blob/main/README.md
# odoo16 has native json-field-support


class JsonField(Field):
    """
    Represents a postgresql Json column (JSON values are mapped to the Python equivalent type of list/dict).
    """
    type = 'json'  # Odoo type of the field (string)
    column_type = ('json', 'json')  # database column type (ident, spec)

    def convert_to_column(self, value, record, values=None, validate=True):
        """ Convert ``value`` from the ``write`` format to the SQL format. """
        # By default the psycopg2 driver does not know how to map dict/list to postgresql json types
        # We need to convert it to the right db type when inserting in the db
        # see https://www.psycopg.org/docs/extras.html
        if value is None:
            return None
        else:
            return psycopg2.extras.Json(value)

    def __init__(self, string, **kwargs):
        self.column_type = ('json', 'json')

        super(JsonField, self).__init__(string= string, **kwargs)

    def convert_to_cache(self, value, record, validate=True):
        if value and not isinstance(value, dict):
            return json.loads(value)
        return value

    def convert_to_record(self, value, record):
        if value:
            return json.dumps(value)
        return value
