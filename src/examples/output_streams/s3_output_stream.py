# Copyright 2022 Edgeworx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Add the AWS SDK library for Python
import boto3

# Add the DarcyAI components that we need, particularly the OutputStream
from darcyai.output.output_stream import OutputStream
from darcyai.utils import validate_not_none, validate_type

# Define our own OutputStream class


class S3Stream(OutputStream):
    """
    A stream that writes data to a AWS S3 bucket.

    """

    def __init__(self,
                 bucket: str,
                 aws_access_key_id: str,
                 aws_secret_access_key: str,
                 aws_region: str):
        # Call init on the parent class
        super().__init__()

        # Validate all input parameters
        validate_not_none(bucket, "bucket is required")
        validate_type(bucket, str, "bucket must be a string")

        validate_not_none(aws_access_key_id, "aws_access_key_id is required")
        validate_type(aws_access_key_id, str,
                      "aws_access_key_id must be a string")

        validate_not_none(aws_secret_access_key,
                          "aws_secret_access_key is required")
        validate_type(aws_secret_access_key, str,
                      "aws_secret_access_key must be a string")

        validate_not_none(aws_region, "aws_region is required")
        validate_type(aws_region, str, "aws_region must be a string")

        # Create an AWS session
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )

        # Choose an S3 bucket as the AWS resource
        s3 = session.resource('s3')
        self.__bucket = s3.Bucket(bucket)

    # Define the "write" method which outputs data on the stream
    def write(self, data: tuple) -> None:
        """
        Writes data to the stream.

        Arguments:
            data (tuple[str, Any]) -- A tuple of the form (key, data)
                where key is the key to write to and data is the data to write.

        Returns:
            None
        """
        if data is None:
            return

        # Validate the incoming data
        validate_type(data, tuple, "data must be a tuple")
        validate_type(data[0], str, "data[0] must be a string")

        # Send up the data using the "put_object" method on the S3 bucket
        key = data[0]
        value = data[1]
        self.__bucket.put_object(Key=key, Body=value)

    # Define the "close" method for the OutputStream object

    def close(self) -> None:
        """
        Closes the output stream.

        Arguments:
            None

        Returns:
            None
        """
        pass
