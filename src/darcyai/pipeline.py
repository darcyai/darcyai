import json
import os
import pathlib
import threading
import time
from collections import OrderedDict
from collections.abc import Iterable
from flask import Flask, request, Response, jsonify, render_template
from json import JSONEncoder
from multiprocessing.pool import ThreadPool
from signal import SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM, SIGQUIT, signal
from typing import Callable, Any, Dict, Tuple, Union, List
from unittest.mock import sentinel

from darcyai.config import Config, RGB
from darcyai.config_registry import ConfigRegistry
from darcyai.cyclic_toposort import acyclic_toposort
from darcyai.input.input_multi_stream import InputMultiStream
from darcyai.input.input_stream import InputStream
from darcyai.log import setup_custom_logger
from darcyai.output.output_stream import OutputStream
from darcyai.perceptor.perceptor import Perceptor
from darcyai.perceptor.perceptor_node import PerceptorNode
from darcyai.perception_object_model import PerceptionObjectModel
from darcyai.processing_engine import ProcessingEngine
from darcyai.stream_data import StreamData
from darcyai.utils import validate_not_none, validate_type, validate


class Pipeline():
    """
    The Pipeline class is the main class of the darcyai package.

    # Arguments
    input_stream (InputStream): The input stream to be used by the pipeline.
    input_data_history_len (int): The number of input data items to be
        stored in the history. Defaults to `1`.
    pom_history_len (int): The number of POM items to be stored in the
        history. Defaults to `1`.
    metrics_history_len (int): The number of metrics items to be stored in
        the history. Defaults to `1`.
    num_of_edge_tpus (int): The number of Edge TPUs. Defaults to `1`.
    perceptor_error_handler_callback (Callable[[str, Exception], None]): The
        callback function to be called when a Perceptor throws
        an exception. Defaults to `None`.
    output_stream_error_handler_callback (Callable[[str, Exception], None]): The
        callback function to be called when an OutputStream
        throws an exception. Defaults to `None`.
    input_stream_error_handler_callback (Callable[[Exception], None]): The
        callback function to be called when an InputStream throws
        an exception. Defaults to `None`.
    perception_completion_callback (Callable[[PerceptionObjectModel], None]): The
        callback function to be called when all the perceptors have completed
        processing. Defaults to `None`.
    universal_rest_api (bool): Whether or not to use the universal
        REST API. Defaults to `False`.
    rest_api_base_path (str): The base path of the REST API. Defaults to `/`.
    rest_api_flask_app (Flask): The Flask application to be used by
        the REST API. Defaults to `None`.
    rest_api_port (int): The port of the REST API. Defaults to `5000`.
    rest_api_host (str): The host of the REST API. Defaults to `localhost`.

    # Examples
    ```python
    >>> from darcyai.input.camera_stream import CameraStream
    >>> from darcyai.pipeline import Pipeline

    >>> camera = CameraStream(video_device="/dev/video0")
    >>> pipeline = Pipeline(input_stream=camera,
    ...                     input_data_history_len=10,
    ...                     pom_history_len=10,
    ...                     metrics_history_len=10,
    ...                     num_of_edge_tpus=1,
    ...                     perceptor_error_handler_callback=None,
    ...                     output_stream_error_handler_callback=None,
    ...                     input_stream_error_handler_callback=None,
    ...                     perception_completion_callback=None,
    ...                     pulse_completion_callback=None,
    ...                     universal_rest_api=True,
    ...                     rest_api_base_path="/",
    ...                     rest_api_flask_app=None,
    ...                     rest_api_port=5000,
    ...                     rest_api_host="localhost")
    ```
    """

    def __init__(self,
                 input_stream: InputStream,
                 input_data_history_len: int = 50,
                 pom_history_len: int = 50,
                 metrics_history_len: int = 50,
                 num_of_edge_tpus: int = 1,
                 perceptor_error_handler_callback: Callable[[str, Exception], None] = None,
                 output_stream_error_handler_callback: Callable[[str, Exception], None] = None,
                 input_stream_error_handler_callback: Callable[[Exception], None] = None,
                 perception_completion_callback: Callable[[PerceptionObjectModel], None] = None,
                 pulse_completion_callback: Callable[[PerceptionObjectModel], None] = None,
                 universal_rest_api: bool = False,
                 rest_api_base_path: str = None,
                 rest_api_flask_app: Flask = None,
                 rest_api_port: int = None,
                 rest_api_host: str = None):
        validate_not_none(input_stream, "input_stream is required")
        validate_type(input_stream, (InputStream, InputMultiStream),
                      "input_stream must be an instance of InputStream")

        validate_type(
            num_of_edge_tpus,
            int,
            "num_of_edge_tpus must be an integer")
        validate(
            num_of_edge_tpus > 0,
            "num_of_edge_tpus must be greater then 0")

        if perceptor_error_handler_callback is not None:
            validate(callable(perceptor_error_handler_callback),
                     "perceptor_error_handler_callback must be a function")

        if output_stream_error_handler_callback is not None:
            validate(callable(output_stream_error_handler_callback),
                     "output_stream_error_handler_callback must be a function")

        if input_stream_error_handler_callback is not None:
            validate(callable(input_stream_error_handler_callback),
                     "input_stream_error_handler_callback must be a function")

        self.__set_perception_completion_callback(perception_completion_callback)

        if pulse_completion_callback is not None:
            validate(callable(pulse_completion_callback),
                     "pulse_completion_callback must be a function")
        self.__pulse_completion_callback = pulse_completion_callback

        if universal_rest_api:
            if rest_api_flask_app is not None:
                validate_type(
                    rest_api_flask_app,
                    Flask,
                    "rest_api_flask_app must be of type Flask")
            else:
                validate_not_none(rest_api_port, "rest_api_port is required")
                validate_type(
                    rest_api_port,
                    int,
                    "rest_api_port must be of type int")
                validate(
                    0 <= rest_api_port <= 65535,
                    "rest_api_port must be between 0 and 65535")

                validate_not_none(rest_api_host, "rest_api_host is required")
                validate_type(
                    rest_api_host,
                    str,
                    "rest_api_host must be a string")

            validate_not_none(
                rest_api_base_path,
                "rest_api_base_path is required")
            validate_type(
                rest_api_base_path,
                str,
                "rest_api_base_path must be a string")

            self.__flask_app = rest_api_flask_app
            self.__port = rest_api_port
            self.__host = rest_api_host
            self.__path = rest_api_base_path

        self.__input_stream = input_stream

        self.__num_of_edge_tpus = num_of_edge_tpus

        self.__input_data_history_len = input_data_history_len
        self.__input_data_history = OrderedDict()

        self.__pom_history_len = pom_history_len
        self.__pom_history = OrderedDict()

        self.__metrics_history = OrderedDict()
        self.__metrics_history_len = metrics_history_len
        self.__average_pipeline_cycle_execution = 0
        self.__average_perceptor_execution = {}
        self.__perceptors_execution_time = {}

        self.__perceptor_error_handler_callback = perceptor_error_handler_callback
        self.__output_stream_error_handler_callback = output_stream_error_handler_callback
        self.__input_stream_error_handler_callback = input_stream_error_handler_callback

        self.__perceptors = {}
        self.__output_streams = {}
        self.__processing_engine = ProcessingEngine(self.__num_of_edge_tpus)
        self.__thread_pool = ThreadPool(10)
        self.__pom = PerceptionObjectModel()
        self.__pulse_number = 0
        self.__perceptor_config_registry = {}
        self.__perceptor_config_schema = {}
        self.__output_config_registry = {}
        self.__output_config_schema = {}
        self.__logger = setup_custom_logger(__name__)

        self.__running = False

        if universal_rest_api:
            threading.Thread(target=self.__start_api_server).start()

        signals = [SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM, SIGQUIT]
        for sig in signals:
            signal(sig, self.stop)

    def num_of_edge_tpus(self) -> int:
        """
        Gets the number of Edge TPUs in the pipeline.

        # Returns
        int: The number of Edge TPUs in the pipeline.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pipeline.num_of_edge_tpus()
        ```
        """
        return self.__num_of_edge_tpus

    def add_perceptor(self,
                      name: str,
                      perceptor: Perceptor,
                      input_callback: Callable[[StreamData,
                                                PerceptionObjectModel,
                                                ConfigRegistry],
                                               Any] = None,
                      output_callback: Callable[[Any,
                                                 PerceptionObjectModel,
                                                 ConfigRegistry],
                                                Any] = None,
                      parent: str = None,
                      multi: bool = False,
                      accelerator_idx: Union[int, None] = None,
                      default_config: Dict[str, Any] = None) -> None:
        """
        Adds a new Perceptor to the pipeline.

        # Arguments
        name (str): The name of the Perceptor (must be a valid variable name).
        perceptor (Perceptor): The Perceptor to be added.
        input_callback (Callable[[StreamData, PerceptionObjectModel, ConfigRegistry], Any]): The
            callback function to be called when the Perceptor receives input data.
            Defaults to `None`.
        output_callback (Callable[[Any, PerceptionObjectModel, ConfigRegistry], Any]): The
            callback function to be called when the Perceptor produces output data.
            Defaults to `None`.
        parent (str): The name of the parent Perceptor. Defaults to `None`.
        multi (bool): Whether or not to run the perceptor for each item in input data.
            Defaults to `False`.
        accelerator_idx (int): The index of the Edge TPU to be used by the Perceptor.
            Defaults to `None`.
        default_config (Dict[str, Any]): The default configuration for the Perceptor.
            Defaults to `None`.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pipeline.add_perceptor(name="perceptor",
        ...                        perceptor=MyPerceptor(),
        ...                        input_callback=None,
        ...                        output_callback=None,
        ...                        parent="input_stream",
        ...                        multi=True,
        ...                        accelerator_idx=0,
        ...                        default_config={"key": "value"})
        ```
        """
        self.__logger.debug("Adding Perceptor '%s' to Pipeline", name)

        self.__validate_perceptor(
            name=name,
            perceptor=perceptor,
            input_callback=input_callback,
            output_callback=output_callback,
            accelerator_idx=accelerator_idx,
            default_config=default_config)

        if parent is not None and parent not in self.__perceptors:
            raise ValueError(
                f"perceptor with name '{parent}' does not exist")

        perceptor_node = PerceptorNode(
            name,
            perceptor,
            input_callback,
            output_callback,
            multi,
            accelerator_idx)

        self.__perceptors[name] = perceptor_node
        if parent is not None:
            self.__perceptors[parent].add_child_perceptor(name)

        self.__create_config_registry_for_perceptor(
            name, perceptor, default_config)

    def add_perceptor_before(self,
                             name_to_insert_before: str,
                             name: str,
                             perceptor: Perceptor,
                             input_callback: Callable[[StreamData,
                                                       PerceptionObjectModel,
                                                       ConfigRegistry],
                                                      Any] = None,
                             output_callback: Callable[[Any,
                                                        PerceptionObjectModel,
                                                        ConfigRegistry],
                                                       Any] = None,
                             multi: bool = False,
                             accelerator_idx: Union[int, None] = None,
                             default_config: dict = None) -> None:
        """
        Adds a new Perceptor to the pipeline.

        # Arguments
        name_to_insert_before (str): The name of the Perceptor to insert the new Perceptor
            before.
        name (str): The name of the Perceptor.
        perceptor (Perceptor): The Perceptor to be added.
        input_callback (Callable[[StreamData, PerceptionObjectModel, ConfigRegistry], Any]): The
            callback function to be called when the Perceptor receives input data.
            Defaults to `None`.
        output_callback (Callable[[Any, PerceptionObjectModel, ConfigRegistry], Any]): The
            callback function to be called when the Perceptor produces output data.
            Defaults to `None`.
        multi (bool): Whether or not to run the perceptor for each item in input data.
            Defaults to `False`.
        accelerator_idx (int): The index of the Edge TPU to be used by the Perceptor.
            Defaults to `None`.
        default_config (dict): The default configuration for the Perceptor.
            Defaults to `None`.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pipeline.add_perceptor_before(name="perceptor",
        ...                               name_to_insert_before="child_input_stream",
        ...                               perceptor=MyPerceptor(),
        ...                               input_callback=None,
        ...                               output_callback=None,
        ...                               multi=True,
        ...                               accelerator_idx=0,
        ...                               default_config={"key": "value"})
        ```
        """
        self.__logger.debug("Adding Perceptor '%s' to Pipeline", name)

        self.__validate_perceptor(
            name=name,
            perceptor=perceptor,
            input_callback=input_callback,
            output_callback=output_callback,
            accelerator_idx=accelerator_idx,
            default_config=default_config)

        validate_not_none(
            name_to_insert_before,
            "name_to_insert_before is required")
        validate_type(
            name_to_insert_before,
            str,
            "name_to_insert_before must be a string")
        validate(
            name_to_insert_before in self.__perceptors,
            f"perceptor with name '{name_to_insert_before}' does not exist")
        validate(name_to_insert_before != name,
                 "name_to_insert_before cannot be the same as name")

        perceptor_node = PerceptorNode(
            name,
            perceptor,
            input_callback,
            output_callback,
            multi,
            accelerator_idx)

        self.__perceptors[name] = perceptor_node

        parents = self.__get_perceptor_parents(name_to_insert_before)
        for parent in parents:
            self.__perceptors[parent].add_child_perceptor(name)
            self.__perceptors[parent].remove_child_perceptor(
                name_to_insert_before)

        self.__perceptors[name].add_child_perceptor(name_to_insert_before)

        self.__create_config_registry_for_perceptor(
            name, perceptor, default_config)

    def add_perceptor_after(self,
                            name_to_insert_after: str,
                            name: str,
                            perceptor: Perceptor,
                            input_callback: Callable[[StreamData,
                                                      PerceptionObjectModel,
                                                      ConfigRegistry],
                                                     Any] = None,
                            output_callback: Callable[[Any,
                                                       PerceptionObjectModel,
                                                       ConfigRegistry],
                                                      Any] = None,
                            multi: bool = False,
                            accelerator_idx: Union[int, None] = None,
                            default_config: dict = None) -> None:
        """
        Adds a new Perceptor to the pipeline.

        # Arguments
        name_to_insert_after (str): The name of the Perceptor to insert the new Perceptor
            after.
        name (str): The name of the Perceptor.
        perceptor (Perceptor): The Perceptor to be added.
        input_callback (Callable[[StreamData, PerceptionObjectModel, Any], ConfigRegistry]): The
            callback function to be called when the Perceptor receives input data.
            Defaults to `None`.
        output_callback (Callable[[Any, PerceptionObjectModel, ConfigRegistry], Any]): The
            callback function to be called when the Perceptor produces output data.
            Defaults to `None`.
        multi (bool): Whether or not to run the perceptor for each item in input data.
            Defaults to `False`.
        accelerator_idx (int): The index of the Edge TPU to be used by the Perceptor.
            Defaults to `None`.
        default_config (dict): The default configuration for the Perceptor.
            Defaults to `None`.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pipeline.add_perceptor_after(name="perceptor",
        ...                               name_to_insert_after="parent_input_stream",
        ...                               perceptor=MyPerceptor(),
        ...                               input_callback=None,
        ...                               output_callback=None,
        ...                               multi=True,
        ...                               accelerator_idx=0,
        ...                               default_config={"key": "value"})
        ```
        """
        self.add_perceptor(
            name=name,
            perceptor=perceptor,
            input_callback=input_callback,
            output_callback=output_callback,
            parent=name_to_insert_after,
            multi=multi,
            accelerator_idx=accelerator_idx,
            default_config=default_config)

    def add_parallel_perceptor(self,
                               name_to_insert_in_parallel_with: str,
                               name: str,
                               perceptor: Perceptor,
                               input_callback: Callable[[StreamData,
                                                         PerceptionObjectModel,
                                                         ConfigRegistry],
                                                        Any] = None,
                               output_callback: Callable[[Any,
                                                          PerceptionObjectModel,
                                                          ConfigRegistry],
                                                         Any] = None,
                               multi: bool = False,
                               accelerator_idx: Union[int, None] = None,
                               default_config: dict = None) -> None:
        """
        Adds a new Perceptor to the pipeline.

        # Arguments
        name_to_insert_in_parallel_with (str): The name of the Perceptor to insert the
            new Perceptor in parallel with.
        name (str): The name of the Perceptor.
        perceptor (Perceptor): The Perceptor to be added.
        input_callback (Callable[[StreamData, PerceptionObjectModel, ConfigRegistry], Any]): The
            callback function to be called when the Perceptor receives input data.
            Defaults to `None`.
        output_callback (Callable[[Any, PerceptionObjectModel, ConfigRegistry], Any]): The
            callback function to be called when the Perceptor produces output data.
            Defaults to `None`.
        multi (bool): Whether or not to run the perceptor for each item in input data.
            Defaults to `False`.
        accelerator_idx (int): The index of the Edge TPU to be used by the Perceptor.
            Defaults to `None`.
        default_config (dict): The default configuration for the Perceptor.
            Defaults to `None`.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pipeline.add_parallel_perceptor(name="perceptor",
        ...                                 name_to_insert_in_parallel_with="parallel_input_stream",
        ...                                 perceptor=MyPerceptor(),
        ...                                 input_callback=None,
        ...                                 output_callback=None,
        ...                                 multi=True,
        ...                                 accelerator_idx=0,
        ...                                 default_config={"key": "value"})
        ```
        """
        self.__logger.debug("Adding Perceptor '%s' to Pipeline", name)

        self.__validate_perceptor(
            name=name,
            perceptor=perceptor,
            input_callback=input_callback,
            output_callback=output_callback,
            accelerator_idx=accelerator_idx,
            default_config=default_config)

        validate_not_none(
            name_to_insert_in_parallel_with,
            "name_to_insert_in_parallel_with is required")
        validate_type(name_to_insert_in_parallel_with, str,
                      "name_to_insert_in_parallel_with must be a string")
        validate(
            name_to_insert_in_parallel_with in self.__perceptors,
            f"perceptor with name '{name_to_insert_in_parallel_with}'" + \
            "does not exist")
        validate(name_to_insert_in_parallel_with != name,
                 "name_to_insert_in_parallel_with cannot be the same as name")

        perceptor_node = PerceptorNode(
            name,
            perceptor,
            input_callback,
            output_callback,
            multi,
            accelerator_idx)

        self.__perceptors[name] = perceptor_node

        parents = self.__get_perceptor_parents(name_to_insert_in_parallel_with)
        for parent in parents:
            self.__perceptors[parent].add_child_perceptor(name)

        self.__create_config_registry_for_perceptor(
            name, perceptor, default_config)

    def update_input_stream(self, input_stream: InputStream) -> None:
        """
        Updates the input stream of the pipeline.

        # Arguments
        input_stream (InputStream): The input stream to be added.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pipeline.update_input_stream(camera)
        """
        self.__logger.debug("Adding Input Stream of type '%s' to Pipeline",
                            input_stream.__class__.__name__)

        validate_not_none(input_stream, "input_stream is required")
        validate_type(input_stream, InputStream, "input_stream must be an InputStream")

        if self.__running:
            raise RuntimeError("Pipeline is already running")

        self.__input_stream = input_stream

    def add_output_stream(self,
                          name: str,
                          callback: Callable[[PerceptionObjectModel,
                                              StreamData],
                                             Any],
                          output_stream: OutputStream,
                          default_config: dict = None) -> None:
        """
        Adds an OutputStream to the pipeline.

        # Arguments
        name (str): The name of the OutputStream.
        callback (Callable[[PerceptionObjectModel, StreamData], Any]): A callback function
            that is called whith PerceptionObjectModel object and returns the data that
            the output stream must process.
        output_stream (OutputStream): The OutputStream to be added.
        default_config (dict): The default configuration for the OutputStream.
            Defaults to `None`.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pipeline.add_output_stream(name="output_stream",
        ...                            callback=None,
        ...                            output_stream=MyOutputStream(),
        ...                            default_config={"key": "value"})
        ```
        """
        self.__logger.debug("Adding OutputStream '%s' to Pipeline", name)

        validate_not_none(name, "name is required")
        validate_type(name, str, "name must be a string")
        validate(name.isidentifier(), "name must be a valid identifier")
        validate(
            name not in self.__output_streams,
            f"output stream with name '{name}' already exists")
        validate(name not in self.__perceptors, "name must be unique")

        validate_not_none(callback, "callback is required")
        validate(callable(callback), "callback must be a function")

        validate_not_none(output_stream, "output_stream is required")
        validate_type(
            output_stream,
            OutputStream,
            "output_stream must be an instance of OutputStream")

        self.__output_streams[name] = {
            "callback": callback,
            "stream": output_stream,
        }

        self.__create_config_registry_for_output_stream(
            name, output_stream, default_config)

    def remove_output_stream(self, name: str) -> None:
        """
        Removes an OutputStream from the pipeline.

        # Arguments
        name (str): The name of the OutputStream to be removed.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)\
        >>> pipeline.add_output_stream(name="output_stream",
        ...                            callback=None,
        ...                            output_stream=MyOutputStream(),
        ...                            default_config={"key": "value"})
        >>> pipeline.remove_output_stream(name="output_stream")
        ```
        """
        self.__logger.debug("Removing OutputStream '%s' from Pipeline", name)

        validate_not_none(name, "name is required")
        validate_type(name, str, "name must be a string")

        if name not in self.__output_streams:
            raise ValueError(
                f"output stream with name '{name}' does not exist")

        del self.__output_streams[name]

    def stop(self) -> None:
        """
        Stops the pipeline.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pipeline.stop()
        ```
        """
        self.__logger.debug("Stopping Pipeline")

        self.__running = False
        self.__input_stream.stop()
        for output_stream in self.__output_streams.values():
            output_stream["stream"].close()

    def run(self) -> None:
        """
        Runs the pipeline.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pipeline.run()
        ```
        """
        self.__logger.debug("Running Pipeline")

        self.__running = True

        pipeline_start_time = time.time()
        pps = 0

        stream = self.__input_stream.stream()
        validate_type(stream, Iterable, "input stream is not Iterable")

        perceptors_order = self.__get_perceptors_order()

        try:
            while True:
                start = time.perf_counter()
                try:
                    input_data = next(stream, sentinel.END_OF_ITERATION)

                    if input_data is sentinel.END_OF_ITERATION:
                        return
                except Exception as e:
                    self.__logger.exception("Error running Pipeline")
                    if self.__input_stream_error_handler_callback is not None:
                        self.__input_stream_error_handler_callback(e)
                    else:
                        raise e

                self.__pulse_number += 1

                # Store input data history
                self.__input_data_history[self.__pulse_number] = input_data
                if len(self.__input_data_history) > self.__input_data_history_len:
                    self.__input_data_history.popitem(last=False)

                pom = PerceptionObjectModel()

                # Run perceptors
                for perceptors in perceptors_order:
                    async_calls = [
                        self.__thread_pool.apply_async(
                            self.__run_perceptor,
                            args=(
                                perceptor_name,
                                input_data,
                                pom),
                            callback=self.__set_perceptor_result(perceptor_name, pom)) \
                        for perceptor_name in perceptors]
                    _ = [async_call.get() for async_call in async_calls]

                pulse_execution_time = time.perf_counter() - start
                pps = int(self.__pulse_number / (time.time() - pipeline_start_time))

                # Calculate metrics
                if self.__pulse_number == 1:
                    self.__average_pipeline_cycle_execution = pulse_execution_time
                else:
                    self.__average_pipeline_cycle_execution = (
                        self.__average_pipeline_cycle_execution *
                        (self.__pulse_number - 1) +
                        pulse_execution_time) / self.__pulse_number

                self.__metrics_history[self.__pulse_number] = {
                    "pulse_execution_time": pulse_execution_time,
                    "perceptors": self.__perceptors_execution_time,
                }
                if len(self.__metrics_history) > self.__metrics_history_len:
                    self.__metrics_history.popitem(last=False)

                # Store pom
                pom.set_input_data(input_data)
                pom.set_pulse_number(self.__pulse_number)
                pom.set_pps(pps)
                self.__pom = pom

                # Store pom history
                self.__pom_history[self.__pulse_number] = self.__pom
                if len(self.__pom_history) > self.__pom_history_len:
                    self.__pom_history.popitem(last=False)

                if self.__perception_completion_callback is not None:
                    self.__perception_completion_callback(pom)

                # Run output streams
                if len(self.__output_streams) > 0:
                    async_calls = [
                        self.__thread_pool.apply_async(
                            self.__run_output_stream,
                            args=[
                                output_stream_name,
                                input_data,
                                pom]) for output_stream_name in self.__output_streams]
                    _ = [async_call.get() for async_call in async_calls]

                self.__pom = pom

                if self.__pulse_completion_callback is not None:
                    self.__pulse_completion_callback(pom)
        finally:
            self.__running = False

    def get_pom(self) -> PerceptionObjectModel:
        """
        Gets the Perception Object Model.

        # Returns
        PerceptionObjectModel: The Perception Object Model.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pom = pipeline.get_pom()
        ```
        """
        return self.__pom

    def get_current_pulse_number(self) -> int:
        """
        Gets the current pulse number.

        # Returns
        int: The current pulse number.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pulse_number = pipeline.get_current_pulse_number()
        ```
        """
        return self.__pulse_number

    def get_latest_input(self) -> StreamData:
        """
        Gets the latest input data.

        # Returns
        StreamData: The latest input data.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> latest_input = pipeline.get_latest_input()
        ```
        """
        return self.__input_data_history[self.__pulse_number]

    def get_historical_input(self, pulse_number: int) -> StreamData:
        """
        Gets the input data from the history.

        # Arguments
        pulse_number (int): The pulse number.

        # Returns
        StreamData: The input data from the history.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> historical_input = pipeline.get_historical_input(pulse_number=1)
        ```
        """
        if pulse_number in self.__input_data_history:
            return self.__input_data_history[pulse_number]
        else:
            return None

    def get_input_history(self) -> Dict[int, StreamData]:
        """
        Gets the input data history.

        # Returns
        `Dict[int, StreamData]` - The input data history.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> input_history = pipeline.get_input_history()
        ```
        """
        return self.__input_data_history.copy()

    def get_historical_pom(self, pulse_number: int) -> PerceptionObjectModel:
        """
        Gets the POM from the history.

        # Arguments
        pulse_number (int): The pulse number.

        # Returns
        PerceptionObjectModel: The POM from the history.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> historical_pom = pipeline.get_historical_pom(pulse_number=1)
        ```
        """
        if pulse_number in self.__pom_history:
            return self.__pom_history[pulse_number]
        else:
            return None

    def get_pom_history(self) -> Dict[int, PerceptionObjectModel]:
        """
        Gets the POM history.

        # Returns
        `Dict[int, PerceptionObjectModel]` - The POM history.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pom_history = pipeline.get_pom_history()
        ```
        """
        return self.__pom_history.copy()

    def run_perceptor(
            self,
            perceptor: Perceptor,
            input_data: Any,
            multi: bool = False) -> Any:
        """
        Runs the Perceptor.

        # Arguments
        perceptor (Perceptor): The Perceptor to be run.
        input_data (Any): The input data.
        multi (bool): Whether or not to run the perceptor for each item in input data.
            Defaults to `False`.

        # Returns
        Any: The result of running the Perceptor.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> result = pipeline.run_perceptor(perceptor=Perceptor(), input_data=None, multi=True)
        ```
        """
        self.__logger.debug("Running custom Perceptor")

        validate_not_none(perceptor, "perceptor is required")
        validate_type(
            perceptor,
            Perceptor,
            "perceptor must be an instance of Perceptor")

        if not perceptor.is_loaded():
            perceptor.load()

        if multi:
            return [perceptor.run(input_data_item, None)
                    for input_data_item in input_data]
        else:
            return perceptor.run(input_data, None)

    def get_graph(self) -> Any:
        """
        Gets the graph of the perceptors.

        # Returns
        Any: The graph of the perceptors.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> graph = pipeline.get_graph()
        ```
        """
        result = {}
        for perceptor in self.__perceptors:
            result[perceptor] = self.__perceptors[perceptor].get_child_perceptors()

        return result

    def get_all_performance_metrics(self) -> Dict[str, Any]:
        """
        Gets the performance metrics of the pipeline.

        # Returns
        `Dict[str, Any]` - The performance metrics of the pipeline.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> metrics = pipeline.get_all_performance_metrics()
        ```
        """
        result = {
            "execution_cycles": self.__pulse_number,
            "average_pipeline_cycle_execution": self.__average_pipeline_cycle_execution,
        }

        perceptors = {}
        for perceptor_name in self.__perceptors:
            perceptors[perceptor_name] = self.__average_perceptor_execution[perceptor_name]
        result["average_perceptor_execution"] = perceptors

        result["history"] = self.__metrics_history
        return result

    def get_pulse_performance_metrics(
            self, pulse_number: Union[int, None] = None) -> Dict[str, Any]:
        """
        Gets the performance metrics of the pipeline for specific pulse.

        # Arguments
        pulse_number (int): The pulse number of the pulse. Defaults to current pulse.
            Defaults to `None`.

        # Returns
        `Dict[str, Any]` - The performance metrics of the pipeline for specific pulse.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> metrics = pipeline.get_pulse_performance_metrics(pulse_number=1)
        ```
        """
        if pulse_number is None:
            pulse_number = self.__pulse_number

        if pulse_number in self.__metrics_history:
            return self.__metrics_history[pulse_number]
        else:
            return None

    def get_perceptor_performance_metrics(
            self, name: str, pulse_number: Union[int, None] = None) -> Dict[str, Any]:
        """
        Gets the performance metrics of the pipeline for specific perceptor.

        # Arguments
        name (str): The name of the perceptor.
        pulse_number (int): The pulse number of the pulse. Defaults to current pulse.
            Defaults to `None`.

        # Returns
        `Dict[str, Any]` - The performance metrics of the pipeline for specific perceptor.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> metrics = pipeline.get_perceptor_performance_metrics(name="perceptor_name",
        ...                                                      pulse_number=1)
        ```
        """
        if name not in self.__perceptors:
            return None

        if pulse_number is None:
            pulse_number = self.__pulse_number

        if pulse_number in self.__metrics_history:
            return self.__metrics_history[pulse_number]["perceptors"][name]
        else:
            return None

    def set_perceptor_config(
            self,
            perceptor_name: str,
            name: str,
            value: Any) -> None:
        """
        Sets the config of the pipeline.

        # Arguments
        perceptor_name (str): The name of the perceptor.
        name (str): The name of the config.
        value (Any): The value of the config.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pipeline.set_perceptor_config(perceptor_name="perceptor_name",
        ...                               name="config_name",
        ...                               value=1)
        ```
        """
        if perceptor_name in self.__perceptor_config_registry:
            self.__validate_and_set_value_for_perceptor_config(
                perceptor_name, name, value)
            self.__perceptors[perceptor_name].set_perceptor_config(name, value)
        else:
            raise Exception(
                f"Perceptor with name '{perceptor_name}' not found")

    def get_perceptor_config(
            self, perceptor_name: str) -> Dict[str, Tuple[Any, Config]]:
        """
        Gets the config of the perceptor.

        # Arguments
        perceptor_name (str): The name of the perceptor.

        # Returns
        `Dict[str, Tuple[Any, Config]]` - The config of the perceptor.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> config = pipeline.get_perceptor_config(perceptor_name="perceptor_name")
        ```
        """
        if perceptor_name not in self.__perceptor_config_registry:
            raise Exception(
                f"Perceptor with name '{perceptor_name}' not found")

        response = {}
        for config_name in self.__perceptor_config_schema[perceptor_name]:
            config_schema = self.__perceptor_config_schema[perceptor_name][config_name]
            response[config_name] = (
                self.__perceptor_config_registry[perceptor_name].get(config_name),
                config_schema)

        return response

    def set_output_stream_config(
            self,
            name: str,
            config_name: str,
            value: Any) -> None:
        """
        Sets the config of the output stream.

        # Arguments
        name (str): The name of the output stream.
        config_name (str): The name of the config.
        value (Any): The value of the config.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> pipeline.set_output_stream_config(name="output_stream_name",
        ...                                   config_name="config_name",
        ...                                   value=1)
        ```
        """
        if name in self.__output_config_registry:
            self.__validate_and_set_value_for_output_stream_config(
                name, config_name, value)
            self.__output_streams[name].set_perceptor_config(
                config_name, value)
        else:
            raise Exception(f"OutputStream with name '{name}' not found")

    def get_output_stream_config(
            self, name: str) -> Dict[str, Tuple[Any, Config]]:
        """
        Gets the config of the output stream.

        # Arguments
        name (str): The name of the output stream.

        # Returns
        `Dict[str, Tuple[Any, Config]]` - The config of the output stream.

        # Examples
        ```python
        >>> from darcyai.input.camera_stream import CameraStream
        >>> from darcyai.pipeline import Pipeline

        >>> camera = CameraStream(video_device="/dev/video0")
        >>> pipeline = Pipeline(input_stream=camera)
        >>> config = pipeline.get_output_stream_config(name="output_stream_name")
        ```
        """
        if name not in self.__output_config_registry:
            raise Exception(f"OutputStream with name '{name}' not found")

        response = {}
        for config_name in self.__output_config_schema[name]:
            config_schema = self.__output_config_schema[name][config_name]
            response[config_name] = (
                self.__output_config_registry[name].get(config_name),
                config_schema)

        return response

    def __run_output_stream(
            self, name: str, input_data: StreamData, pom: PerceptionObjectModel) -> None:
        """
        Runs the output stream.

        # Arguments
        name (str): The name of the output stream.
        input_data (StreamData): The input data.
        pom (PerceptionObjectModel): The pom.
        """
        try:
            processed_data = self.__output_streams[name]["callback"](
                pom, input_data)
            output = self.__output_streams[name]["stream"].write(processed_data)
            pom.set_value(name, output)
        except Exception as e:
            self.__logger.exception("Error running output stream '%s'", name)
            if self.__output_stream_error_handler_callback is not None:
                self.__output_stream_error_handler_callback(name, e)
            else:
                raise e

    def __run_perceptor(
            self, name: str, input_data: StreamData, pom: PerceptionObjectModel) -> None:
        """
        Runs the perceptor.

        # Arguments
        name (str): The name of the perceptor.
        input_data (StreamData): The input data.
        pom (PerceptionObjectModel): The pom.
        """
        start = time.perf_counter()
        try:
            return self.__processing_engine.run(
                self.__perceptors[name],
                input_data,
                pom,
                self.__perceptor_config_registry[name])
        except Exception as e:
            self.__logger.exception("Error running perceptor '%s'", name)
            if self.__perceptor_error_handler_callback is not None:
                self.__perceptor_error_handler_callback(name, e)
            else:
                raise e
        finally:
            execution_time = time.perf_counter() - start
            self.__perceptors_execution_time[name] = {
                "execution_time": execution_time,
            }
            if name in self.__average_perceptor_execution:
                avg_perceptors_execution = self.__average_perceptor_execution[name]
                self.__average_perceptor_execution[name] = (
                    avg_perceptors_execution *
                    (self.__pulse_number - 1) +
                    execution_time) / self.__pulse_number
            else:
                self.__average_perceptor_execution[name] = execution_time

    def __set_perceptor_result(
            self, perceptor_name: str, pom: PerceptionObjectModel) -> Callable[[Any], None]:
        """
        Sets the result of the perceptor.

        # Arguments
        perceptor_name (str): The name of the perceptor.
        pom (PerceptionObjectModel): The pom.

        # Returns
        Callable[[Any], None]: The callback function.
        """
        def set_result(result: Any) -> None:
            """
            Sets the result of the perceptor.

            # Arguments
            result (Any): The result of the perceptor.
            """
            pom.set_value(perceptor_name, result)

        return set_result

    def __get_perceptors_order(self) -> List[str]:
        """
        Gets the topological order of the perceptors.

        # Returns
        [str]: The order of the perceptors.
        """
        orphan_perceptors = []
        parent_perceptors = []
        visited = []

        for perceptor_name in self.__perceptors:
            child_perceptors = self.__perceptors[perceptor_name].get_child_perceptors(
            )
            if len(child_perceptors) == 0:
                if perceptor_name not in visited:
                    orphan_perceptors.append(perceptor_name)
            else:
                visited.append(perceptor_name)
                for child in child_perceptors:
                    parent_perceptors.append((perceptor_name, child))
                    visited.append(child)

        if len(parent_perceptors) > 0:
            perceptors_order = acyclic_toposort(parent_perceptors)
            _ = [perceptors_order[0].add(x) for x in orphan_perceptors]
        else:
            perceptors_order = [orphan_perceptors]

        return perceptors_order

    def __validate_perceptor(self,
                             name: str,
                             perceptor: Perceptor,
                             input_callback:
                                Callable[[StreamData, PerceptionObjectModel], Any] = None,
                             output_callback: Callable[[Any, PerceptionObjectModel], Any] = None,
                             accelerator_idx: Union[int, None] = None,
                             default_config: dict = None) -> None:
        """
        Validates the perceptor.

        # Arguments
        name (str): The name of the perceptor.
        perceptor (Perceptor): The perceptor.
        input_callback (Callable[[StreamData, PerceptionObjectModel], Any]): The
            callback function for the input stream. Default is `None`.
        output_callback (Callable[[Any, PerceptionObjectModel], Any]): The
            callback function for the output stream. Default is `None`.
        accelerator_idx (int): The index of the accelerator. Defaults to `None`.
        default_config (dict): The default config. Defaults to `None`.
        """
        if self.__running:
            raise Exception("Pipeline is already running")

        validate_not_none(name, "name is required")
        validate_type(name, str, "name must be a string")
        validate(name.isidentifier(), "name must be a valid identifier")
        validate(name not in self.__perceptors, "name must be unique")
        validate(name not in self.__output_streams, "name must be unique")

        validate_not_none(perceptor, "perceptor is required")
        validate_type(
            perceptor,
            Perceptor,
            "perceptor must be an instance of Perceptor")

        if input_callback is not None:
            validate_not_none(input_callback, "input_callback is required")
            validate(callable(input_callback), "input_callback must be a function")

        if output_callback is not None:
            validate(
                callable(output_callback),
                "output_callback must be a function")

        if accelerator_idx is not None:
            validate_type(
                accelerator_idx,
                int,
                "accelerator_idx must be an integer")

            if accelerator_idx >= self.__num_of_edge_tpus:
                raise ValueError(
                    f"accelerator_idx must be >= 0 and < {self.__num_of_edge_tpus}")

        if default_config is not None:
            validate_type(
                default_config,
                dict,
                "default_config must be a dictionary")

    def __get_perceptor_parents(self, perceptor_name: str) -> List[str]:
        """
        Gets the parents of the perceptor.

        # Arguments
        perceptor_name (str): The name of the perceptor.

        # Returns
        [str]: The parents of the perceptor.
        """
        parent_perceptors = []
        for parent_perceptor_name in self.__perceptors:
            child_perceptors = self.__perceptors[parent_perceptor_name].get_child_perceptors(
            )
            if perceptor_name in child_perceptors:
                parent_perceptors.append(parent_perceptor_name)

        return parent_perceptors

    def __create_config_registry_for_perceptor(
            self,
            perceptor_name: str,
            perceptor: Perceptor,
            default_config: dict = None) -> None:
        """
        Creates the config registry for the perceptor.

        # Arguments
        perceptor_name (str): The name of the perceptor.
        perceptor (Perceptor): The perceptor.
        default_config (dict): The default config. Defaults to `None`.
        """
        self.__perceptor_config_registry[perceptor_name] = ConfigRegistry()

        perceptor_config_schema = perceptor.get_config_schema()
        config_schema_dict = {}
        for config_schema in perceptor_config_schema:
            validate_type(
                config_schema,
                Config,
                "config_schema must be an instance of Config")
            config_schema_dict[config_schema.name] = config_schema
            self.__perceptor_config_registry[perceptor_name].set_value(
                config_schema.name, config_schema.default_value)
        self.__perceptor_config_schema[perceptor_name] = config_schema_dict

        if default_config is not None:
            for name, value in default_config.items():
                self.__validate_and_set_value_for_perceptor_config(
                    perceptor_name, name, value)

    def __validate_and_set_value_for_perceptor_config(
            self, perceptor_name: str, config_name: str, value: Any) -> None:
        """
        Validates and sets the value for the perceptor config.

        # Arguments
        perceptor_name (str): The name of the perceptor.
        config_name (str): The name of the config.
        value (Any): The value of the config.
        """
        config_schema_dict = self.__perceptor_config_schema[perceptor_name]
        if config_name not in config_schema_dict:
            return

        config_schema = config_schema_dict[config_name]

        converted_value = value
        if config_schema.type == "rgb" and isinstance(value, str):
            if value[0] == "#":
                converted_value = RGB.from_hex_string(value)
            else:
                converted_value = RGB.from_string(value)

        if not config_schema.is_valid(converted_value):
            raise ValueError(f"Invalid value for config '{config_name}'")

        self.__perceptor_config_registry[perceptor_name].set_value(
            config_name, converted_value)
        self.__perceptors[perceptor_name].set_perceptor_config(
            config_name, converted_value)

    def __start_api_server(self) -> None:
        """
        Starts the API server.
        """
        script_dir = pathlib.Path(__file__).parent.absolute()
        swagger_path = os.path.join(script_dir, "swagger")
        if self.__flask_app is None:
            self.__flask_app = Flask(__name__,
                static_folder=os.path.join(swagger_path, "static"),
                template_folder=os.path.join(swagger_path, "templates"))
            ssl_context = None
            self.__setup_paths()
            self.__flask_app.json_encoder = CustomJSONEncoder
            self.__flask_app.run(
                host=self.__host,
                port=self.__port,
                ssl_context=ssl_context,
                debug=False)
        else:
            self.__setup_paths()
            self.__flask_app.json_encoder = CustomJSONEncoder

    def __setup_paths(self) -> None:
        """
        Sets up the paths.
        """
        paths = {
            "/perceptors": {
                "methods": ["GET"],
                "function": self.__get_perceptors,
            },
            "/outputs": {
                "methods": ["GET"],
                "function": self.__get_outputs,
            },
            "/perceptors/config": {
                "methods": ["GET", "PATCH"],
                "function": self.__modify_perceptors_config_registry,
            },
            "/perceptors/<perceptor>/config": {
                "methods": ["GET", "PATCH"],
                "function": self.__modify_perceptor_config_registry,
            },
            "/outputs/config": {
                "methods": ["GET", "PATCH"],
                "function": self.__modify_outputs_config_registry,
            },
            "/outputs/<output_stream>/config": {
                "methods": ["GET", "PATCH"],
                "function": self.__modify_output_config_registry,
            },
            "/swagger": {
                "methods": ["GET"],
                "function": self.__swagger,
            },
            "/specs": {
                "methods": ["GET"],
                "function": self.__specs,
            },
        }

        for path, path_config in paths.items():
            complete_path = self.__path + path

            add = True
            for rule in self.__flask_app.url_map.iter_rules():
                if rule.rule == complete_path:
                    add = False
                    break

            if not add:
                continue

            self.__flask_app.add_url_rule(
                complete_path,
                complete_path,
                path_config["function"],
                methods=path_config["methods"])

    def __get_perceptors(self) -> Response:
        """
        Gets the perceptors.

        # Returns
        Response: The response.
        """
        perceptors = self.__perceptors.keys()
        return jsonify(list(perceptors))

    def __get_outputs(self) -> Response:
        """
        Gets the outputs.

        # Returns
        Response: The response.
        """
        output_streams = self.__output_streams.keys()
        return jsonify(list(output_streams))

    def __modify_perceptors_config_registry(self) -> Response:
        """
        Modifies the perceptors config registry.

        # Returns
        Response: The response.
        """
        errors = []
        if request.method == "PATCH":
            body = self.__get_body()
            for perceptor_name, values in body.items():
                if perceptor_name not in self.__perceptors:
                    return Response(
                        f"perceptor with name {perceptor_name} does not exist",
                        status=404)

                for name, value in values.items():
                    try:
                        self.__validate_and_set_value_for_perceptor_config(
                            perceptor_name, name, value)
                    except BaseException:
                        errors.append(f"Invalid value for config '{name}'")
                        pass

        if len(errors) > 0:
            return jsonify(errors), 400

        cfgs = {}
        for perceptor_name in self.__perceptors:
            cfgs[perceptor_name] = []
            for config_name in self.__perceptor_config_schema[perceptor_name]:
                config_schema = self.__perceptor_config_schema[perceptor_name][config_name]
                cfgs[perceptor_name].append({
                    "name": config_name,
                    "value": self.__perceptor_config_registry[perceptor_name].get(config_name),
                    "type": config_schema.type,
                    "description": config_schema.description,
                    "default_value": config_schema.default_value,
                })

        return jsonify(cfgs)

    def __modify_perceptor_config_registry(self, **kwargs) -> Response:
        """
        Modifies the perceptor config registry.

        # Arguments
        **kwargs: The keyword arguments.

        # Returns
        Response: The response.
        """
        perceptor_name = kwargs["perceptor"]

        if perceptor_name not in self.__perceptors:
            return Response(
                f"perceptor with name {perceptor_name} does not exist", status=404)

        errors = []
        if request.method == "PATCH":
            body = self.__get_body()
            for name, value in body.items():
                try:
                    self.__validate_and_set_value_for_perceptor_config(
                        perceptor_name, name, value)
                except BaseException:
                    errors.append(f"Invalid value for config '{name}'")
                    pass

        if len(errors) > 0:
            return jsonify(errors), 400

        cfgs = []
        for config_name in self.__perceptor_config_schema[perceptor_name]:
            config_schema = self.__perceptor_config_schema[perceptor_name][config_name]
            cfgs.append({
                "name": config_name,
                "value": self.__perceptor_config_registry[perceptor_name].get(config_name),
                "type": config_schema.type,
                "description": config_schema.description,
                "default_value": config_schema.default_value,
            })

        return jsonify(cfgs)

    def __modify_outputs_config_registry(self) -> Response:
        """
        Modifies the outputs config registry.

        # Returns
        Response: The response.
        """
        errors = []
        if request.method == "PATCH":
            body = self.__get_body()
            for output_name, values in body.items():
                if output_name not in self.__output_streams:
                    return Response(
                        f"output stream with name {output_name} does not exist", status=404)

                for name, value in values.items():
                    try:
                        self.__validate_and_set_value_for_output_stream_config(
                            output_name, name, value)
                    except BaseException:
                        errors.append(f"Invalid value for config '{name}'")
                        pass

        if len(errors) > 0:
            return jsonify(errors), 400

        cfgs = {}
        for output_name in self.__output_streams:
            cfgs[output_name] = []
            for config_name in self.__output_config_schema[output_name]:
                config_schema = self.__output_config_schema[output_name][config_name]
                cfgs[output_name].append({
                    "name": config_name,
                    "value": self.__output_config_registry[output_name].get(config_name),
                    "type": config_schema.type,
                    "description": config_schema.description,
                    "default_value": config_schema.default_value,
                })

        return jsonify(cfgs)

    def __modify_output_config_registry(self, **kwargs) -> Response:
        """
        Modifies the output config registry.

        # Arguments
        **kwargs: The keyword arguments.

        # Returns
        Response: The response.
        """
        output_name = kwargs["output_stream"]

        if output_name not in self.__output_streams:
            return Response(
                f"output stream with name {output_name} does not exist", status=404)

        errors = []
        if request.method == "PATCH":
            body = self.__get_body()
            for name, value in body.items():
                try:
                    self.__validate_and_set_value_for_output_stream_config(
                        output_name, name, value)
                except BaseException:
                    errors.append(f"Invalid value for config '{name}'")
                    pass

        if len(errors) > 0:
            return jsonify(errors), 400

        cfgs = []
        for config_name in self.__output_config_schema[output_name]:
            config_schema = self.__output_config_schema[output_name][config_name]
            cfgs.append({
                "name": config_name,
                "value": self.__output_config_registry[output_name].get(config_name),
                "type": config_schema.type,
                "description": config_schema.description,
                "default_value": config_schema.default_value,
            })

        return jsonify(cfgs)

    def __create_config_registry_for_output_stream(
            self,
            name: str,
            output_stream: OutputStream,
            default_config: dict = None) -> None:
        """
        Creates the config registry for an output stream.

        # Arguments
        name: The name of the output stream.
        output_stream: The output stream.
        default_config: The default config. Defaults to `None`.
        """
        self.__output_config_registry[name] = ConfigRegistry()

        output_stream_config_schema = output_stream.get_config_schema()
        config_schema_dict = {}
        for config_schema in output_stream_config_schema:
            validate_type(
                config_schema,
                Config,
                "config_schema must be an instance of Config")
            config_schema_dict[config_schema.name] = config_schema
            self.__output_config_registry[name].set_value(
                config_schema.name, config_schema.default_value)
        self.__output_config_schema[name] = config_schema_dict

        if default_config is not None:
            for config_name, value in default_config.items():
                self.__validate_and_set_value_for_output_stream_config(
                    name, config_name, value)

    def __validate_and_set_value_for_output_stream_config(
            self, name: str, config_name: str, value: Any) -> None:
        """
        Validates and sets the value for an output stream config.

        # Arguments
        name: The name of the output stream.
        config_name: The name of the config.
        value: The value.
        """
        config_schema_dict = self.__output_config_schema[name]
        if config_name not in config_schema_dict:
            return

        config_schema = config_schema_dict[config_name]
        if not config_schema.is_valid(value):
            raise ValueError(f"Invalid value for config '{config_name}'")

        self.__output_config_registry[name].set_value(config_name, value)
        self.__output_streams[name]["stream"].set_config_value(
            config_name, value)

    def __get_body(self):
        """
        Gets the body.

        # Returns
        dict: The body.
        """
        if isinstance(request.json, str):
            return json.loads(request.json)
        else:
            validate_type(request.json, dict, "request body must be a JSON")
            return request.json

    def __swagger(self) -> Response:
        """
        Swagger.

        # Returns
        Response: The response.
        """
        return render_template("swaggerui.html", base_path=self.__path)

    def __specs(self) -> Response:
        """
        OpenAPI 2.0 specs.

        # Returns
        Response: The response.
        """
        return render_template("openapi.json", base_path=self.__path)

    def __set_perception_completion_callback(
            self, perception_completion_callback: Callable[[PerceptionObjectModel], None] = None):
        """
        Sets the perception completion callback.

        # Arguments
        perception_completion_callback: The perception completion callback.
        """
        if perception_completion_callback is not None:
            validate(callable(perception_completion_callback),
                     "perception_completion_callback must be a function")

        self.__perception_completion_callback = perception_completion_callback

class CustomJSONEncoder(JSONEncoder):
    """
    Custom JSON encoder.
    """

    def default(self, o):
        """
        Default.

        # Arguments
        o: The object.

        # Returns
        Any: The result.
        """
        if isinstance(o, RGB):
            return o.to_hex()
        else:
            return super().default(o)
