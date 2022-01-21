import threading
from typing import Any, Union, List

from darcyai.log import setup_custom_logger
from darcyai.perceptor.perceptor_node import PerceptorNode
from darcyai.perception_object_model import PerceptionObjectModel
from darcyai.config_registry import ConfigRegistry
from darcyai.stream_data import StreamData


class ProcessingEngine():
    """
    The ProcessingEngine class is responsible for running perceptors
        on Edge TPUs

    # Arguments
    number_of_edge_tpus (int): The number of Edge TPUs to use
    """

    def __init__(self, number_of_edge_tpus: int):
        self.__edge_tpu_locks = [threading.Lock()
                                 for _ in range(number_of_edge_tpus)]
        self.__logger = setup_custom_logger(__name__)

    def run(self,
            perceptor_node: PerceptorNode,
            input_data: StreamData,
            pom: PerceptionObjectModel,
            config: ConfigRegistry = None) -> Union[Any, List[Any]]:
        """
        Runs the perceptor on the input data

        # Arguments
        perceptor_node (PerceptorNode): The perceptor node to run
        input_data (StreamData): The input data to run the perceptor on
        pom (PerceptionObjectModel): The perception object model to use
        config (ConfigRegistry): The config registry to use. Defaults to `None`.

        # Returns
        Any: The output of the perceptor
        """
        if perceptor_node.accelerator_idx is not None:
            self.__edge_tpu_locks[perceptor_node.accelerator_idx].acquire()

        self.__logger.debug("running %s", perceptor_node)

        try:
            processed_data = perceptor_node.process_input_data(input_data, pom, config)
            if perceptor_node.multi:
                return [perceptor_node.run(data, pom, config)
                        for data in processed_data]
            else:
                return perceptor_node.run(processed_data, pom, config)
        finally:
            if perceptor_node.accelerator_idx is not None:
                self.__edge_tpu_locks[perceptor_node.accelerator_idx].release()
