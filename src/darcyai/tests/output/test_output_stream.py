# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

from darcyai.output.output_stream import OutputStream


class TestOutputStream:
    """
    OutputStream tests.
    """
    def test_constructor(self):
        output_stream = OutputStream()
        assert output_stream is not None
