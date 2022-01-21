import csv
import io

from darcyai.file_stream import FileStream
from darcyai.output.output_stream import OutputStream
from darcyai.utils import validate_not_none, validate_type


class CSVOutputStream(OutputStream):
    """
    OutputStream implementation that writes to a CSV file.

    # Arguments
    file_path (str): The path to the CSV file to write to.
    delimiter (str): The delimiter to use in the CSV file. Defaults to `,`.
    quotechar (str): The quote character to use in the CSV file. Defaults to `|`.
    buffer_size (int): The size of the buffer to use when writing to theCSV file.
        Defaults to `0`.
    flush_interval (int): The number of seconds before flushing the buffer to disk.
        Defaults to `0`.

    # Examples
    ```python
    >>> from darcyai.output.csv_output_stream import CSVOutputStream
    >>> csv_output_stream = CSVOutputStream(file_path="output.csv",
                                            delimiter=",",
                                            quotechar="|",
                                            buffer_size=1024*1024,
                                            flush_interval=0)
    ```
    """

    def __init__(
            self,
            file_path: str,
            delimiter: str = ",",
            quotechar: str = "|",
            buffer_size: int = 0,
            flush_interval: int = 0) -> None:
        super().__init__()

        validate_not_none(file_path, "file_path is required")
        validate_type(file_path, str, "file_path must be a string")

        validate_not_none(delimiter, "delimiter is required")
        validate_type(delimiter, str, "delimiter must be a string")

        validate_not_none(quotechar, "quotechar is required")
        validate_type(quotechar, str, "quotechar must be a string")

        self.__file_stream = FileStream(
            file_path,
            buffer_size=buffer_size,
            flush_interval=flush_interval)

        self.__delimiter = delimiter
        self.__quotechar = quotechar
        self.__delimiter = delimiter
        self.__quotechar = quotechar

        self.config_schema = []

    def write(self, data: list) -> None:
        """
        Writes the given data to the CSV file.

        # Arguments
        data (list): The data to write to the CSV file.

        # Examples
        ```python
        >>> from darcyai.output.csv_output_stream import CSVOutputStream
        >>> csv_output_stream = CSVOutputStream(file_path="output.csv",
                                                delimiter=",",
                                                quotechar="|",
                                                buffer_size=1024*1024,
                                                flush_interval=0)
        >>> csv_output_stream.write([["a", "b", "c"], ["d", "e", "f"]])
        ```
        """
        if data is None:
            return

        validate_type(data, list, "data must be a list")

        output = io.StringIO()
        csv_writer = csv.writer(
            output,
            delimiter=self.__delimiter,
            quotechar=self.__quotechar)

        csv_writer.writerow(data)

        self.__file_stream.write_string(output.getvalue())

    def close(self) -> None:
        """
        Closes the CSV file.

        # Examples
        ```python
        >>> from darcyai.output.csv_output_stream import CSVOutputStream
        >>> csv_output_stream = CSVOutputStream(file_path="output.csv",
                                                delimiter=",",
                                                quotechar="|",
                                                buffer_size=1024*1024,
                                                flush_interval=0)
        >>> csv_output_stream.close()
        ```
        """
        self.__file_stream.close()
