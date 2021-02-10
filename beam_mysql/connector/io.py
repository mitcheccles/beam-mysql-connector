"""I/O connectors of mysql."""

from typing import Dict
from typing import Union

import apache_beam as beam
from apache_beam.io import iobase
from apache_beam.options.value_provider import ValueProvider
from apache_beam.pvalue import PCollection
from apache_beam.transforms.core import PTransform

from beam_mysql.connector import splitters
from beam_mysql.connector.client import MySQLClient
from beam_mysql.connector.source import MySQLSource
from beam_mysql.connector.utils import get_runtime_value


class ReadFromMySQL(PTransform):
    """Create PCollection from MySQL."""

    def __init__(
        self,
        query: Union[str, ValueProvider],
        host: Union[str, ValueProvider],
        database: Union[str, ValueProvider],
        user: Union[str, ValueProvider],
        password: Union[str, ValueProvider],
        port: Union[int, ValueProvider] = 3306,
        splitter=splitters.NoSplitter(),
    ):
        super().__init__()
        self._query = query
        self._host = host
        self._database = database
        self._user = user
        self._password = password
        self._port = port
        self._splitter = splitter

    def expand(self, pcoll: PCollection) -> PCollection:
        return pcoll | iobase.Read(
            MySQLSource(self._query, self._host, self._database, self._user, self._password, self._port, self._splitter)
        )


class WriteToMySQL(PTransform):
    """Write dict rows to MySQL."""

    def __init__(
        self,
        host: Union[str, ValueProvider],
        database: Union[str, ValueProvider],
        table: Union[str, ValueProvider],
        user: Union[str, ValueProvider],
        password: Union[str, ValueProvider],
        write_columns: list,
        port: Union[int, ValueProvider] = 3306,
        batch_size: int = 1000
    ):
        super().__init__()
        self._host = host
        self._database = database
        self._table = table
        self._user = user
        self._password = password
        self._write_columns = write_columns
        self._port = port
        self._batch_size = batch_size

    def expand(self, pcoll: PCollection) -> PCollection:
        return pcoll | beam.ParDo(
            _WriteToMySQLFn(
                self._host, self._database, self._table, self._user, self._password, self._write_columns, self._port, self._batch_size
            )
        )


class _WriteToMySQLFn(beam.DoFn):
    """DoFn for WriteToMySQL."""

    def __init__(
        self,
        host: Union[str, ValueProvider],
        database: Union[str, ValueProvider],
        table: Union[str, ValueProvider],
        user: Union[str, ValueProvider],
        password: Union[str, ValueProvider],
        write_columns: list,
        port: Union[int, ValueProvider],
        batch_size: int,
    ):
        super().__init__()
        self._host = host
        self._database = database
        self._table = table
        self._user = user
        self._password = password
        self._port = port
        self._write_columns = write_columns
        self._batch_size = batch_size
        self._prepared_statement = self.__build_prepared_statement()

        self._config = {
            "host": self._host,
            "database": self._database,
            "user": self._user,
            "password": self._password,
            "port": self._port,
        }

    def __build_prepared_statement(self):
        return """
        INSERT INTO {table} ({columns}) VALUES ({values})
        """.format(
            table=self._table,
            columns=",".join(self._write_columns),
            values=",".join(["%s" for x in self._write_columns])
            )

    def start_bundle(self):
        self._build_value()
        self._queries = []

    def process(self, element: Dict, *args, **kwargs):
        query = []
        for col in self._write_columns:
            query.append(element[col])

        self._queries.append(query)

        if len(self._queries) > self._batch_size:
            self._client.record_loader(self._prepared_statement, self._queries)
            self._queries.clear()

    def finish_bundle(self):
        if len(self._queries):
            self._client.record_loader(self._prepared_statement, self._queries)
            self._queries.clear()

    def _build_value(self):
        for k, v in self._config.items():
            self._config[k] = get_runtime_value(v)
        self._table = get_runtime_value(self._table)
        self._batch_size = get_runtime_value(self._batch_size)

        self._client = MySQLClient(self._config)
