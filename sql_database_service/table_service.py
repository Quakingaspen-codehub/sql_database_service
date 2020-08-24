from . import QueryStatus
from sqlalchemy import desc


class TableService:
    def __init__(self, database, table=None, per_page=10):
        self.database = database
        self.table = table
        self.per_page = per_page

    def query(self, row_filter=None, column_filter=list(), group_by=None, order_by=dict()):

        query = self.table.query

        # Rows filtering
        if row_filter is not None:
            query = query.filter(row_filter)

        # Columns filtering
        if len(column_filter) > 0:
            query = query.with_entities(*column_filter)

        # Grouping
        if group_by:
            query = query.group_by(group_by)

        # Ordering
        if len(order_by) > 0:
            req_col = order_by['column'] if order_by['ascending'] else desc(order_by['column'])
            query = query.order_by(req_col)

        return query

    @QueryStatus.get_query_status
    def read(self, row_filter=None, column_filter=list(), group_by=None, order_by=dict(),
             count='first', page=None):
        """ Return query records """

        query = self.query(row_filter, column_filter, group_by, order_by)

        if count == 'first':
            return self, query.first()

        if page is None:
            return self, query.all()

        else:
            pager = query.paginate(per_page=self.per_page, page=page)
            return self, {'page': pager.items, 'num_pages': pager.pages}

    @QueryStatus.get_query_status
    def count(self, row_filter=None, column_filter=list()):
        """ Return number of records per query """
        query = self.query(row_filter, column_filter)
        return self, query.count()

    @QueryStatus.get_query_status
    def is_available(self, row_filter):
        """ Check if a record is available """

        qs = self.count(row_filter)
        return self, qs.data > 0

    @QueryStatus.get_query_status
    def create(self, new_record):
        """ Create a new record
            new_record: is an object of the model type
        """

        self.database.session.add(new_record)
        self.commit()
        return self, None

    @QueryStatus.get_query_status
    def update(self, id_, updated_record):
        """ Update an existing record
            updated_record: is a dictionary
        """

        query = self.query(self.table.id == id_)
        query.update(updated_record)
        self.commit()
        return self, None

    @QueryStatus.get_query_status
    def delete(self, id_):
        """ Delete an existing record """

        qs = self.read(self.table.id == id_)
        self.database.session.delete(qs.data)
        self.commit()
        return self, None

    def commit(self):
        try:
            self.database.session.commit()

        except Exception as e:
            self.database.session.rollback()
            raise e
