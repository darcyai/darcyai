import json
import requests
import time

from darcyai.pipeline import Pipeline
from .sample_input_stream import SampleInputStream
from .sample_output_stream import SampleOutputStream
from .sample_perceptor import SamplePerceptor


class Test():
    def __init__(self):
        ping = SampleInputStream(max_runs=2)
        output_stream = SampleOutputStream()

        self.__pipeline = Pipeline(input_stream=ping,
                                   input_stream_error_handler_callback=self.__input_stream_error_handler_callback,
                                   universal_rest_api=True,
                                   rest_api_base_path="/pipeline",
                                   rest_api_port=8080,
                                   rest_api_host="0.0.0.0")

        self.__pipeline.add_output_stream("output", self.__output_stream_callback, output_stream)

        perceptor = SamplePerceptor(sleep=0.5)
        self.__pipeline.add_perceptor("perceptor", perceptor, input_callback=self.__perceptor_input_callback)

        time.sleep(1)

    def act(self):
        pass

    def verify(self):
        base_url = "http://localhost:8080/pipeline"

        response = requests.request(
            "GET",
            f"{base_url}/perceptors")
        json_response = response.json()
        assert response.status_code == 200
        assert len(json_response) == 1
        assert json_response[0] == "perceptor"

        base_url = "http://localhost:8080/pipeline"
        response = requests.request(
            "GET",
            f"{base_url}/perceptors/config")
        json_response = response.json()
        assert response.status_code == 200
        assert "perceptor" in json_response
        self.__validate_perceptor_config(json_response["perceptor"])

        base_url = "http://localhost:8080/pipeline"
        response = requests.request(
            "GET",
            f"{base_url}/perceptors/perceptor/config")
        json_response = response.json()
        assert response.status_code == 200
        self.__validate_perceptor_config(json_response)

        base_url = "http://localhost:8080/pipeline"
        response = requests.request(
            "PATCH",
            f"{base_url}/perceptors/config",
            json=json.dumps({ "perceptor": { "bool_config": True } }),
            headers={'Content-Type': 'application/json'})
        json_response = response.json()
        assert response.status_code == 200
        self.__validate_perceptor_config(json_response["perceptor"])
        assert json_response["perceptor"][0]["default_value"] == False
        assert json_response["perceptor"][0]["value"] == True

        base_url = "http://localhost:8080/pipeline"
        response = requests.request(
            "PATCH",
            f"{base_url}/perceptors/perceptor/config",
            json=json.dumps({ "bool_config": True }),
            headers={'Content-Type': 'application/json'})
        json_response = response.json()
        assert response.status_code == 200
        self.__validate_perceptor_config(json_response)
        assert json_response[0]["default_value"] == False
        assert json_response[0]["value"] == True

        response = requests.request(
            "GET",
            f"{base_url}/outputs")
        json_response = response.json()
        assert response.status_code == 200
        assert len(json_response) == 1
        assert json_response[0] == "output"

        base_url = "http://localhost:8080/pipeline"
        response = requests.request(
            "GET",
            f"{base_url}/outputs/config")
        json_response = response.json()
        assert response.status_code == 200
        assert "output" in json_response
        self.__validate_output_config(json_response["output"])

        base_url = "http://localhost:8080/pipeline"
        response = requests.request(
            "GET",
            f"{base_url}/outputs/output/config")
        json_response = response.json()
        assert response.status_code == 200
        self.__validate_output_config(json_response)

        base_url = "http://localhost:8080/pipeline"
        response = requests.request(
            "PATCH",
            f"{base_url}/outputs/config",
            json=json.dumps({ "output": { "test": True } }),
            headers={'Content-Type': 'application/json'})
        json_response = response.json()
        assert response.status_code == 200
        self.__validate_output_config(json_response["output"])
        assert json_response["output"][0]["default_value"] == False
        assert json_response["output"][0]["value"] == True

        base_url = "http://localhost:8080/pipeline"
        response = requests.request(
            "PATCH",
            f"{base_url}/outputs/output/config",
            json=json.dumps({ "test": True }),
            headers={'Content-Type': 'application/json'})
        json_response = response.json()
        assert response.status_code == 200
        self.__validate_output_config(json_response)
        assert json_response[0]["default_value"] == False
        assert json_response[0]["value"] == True

    def cleanup(self):
        pass

    def __perceptor_input_callback(self, input_data, pom, config):
        return input_data

    def __output_stream_callback(self, pom, input_data):
        pass

    def __input_stream_error_handler_callback(self, exception):
        pass

    def __validate_perceptor_config(self, perceptor_config):
        assert len(perceptor_config) == 4
        assert perceptor_config[0]["name"] == "bool_config"
        assert perceptor_config[1]["name"] == "int_config"
        assert perceptor_config[2]["name"] == "float_config"
        assert perceptor_config[3]["name"] == "str_config"

    def __validate_output_config(self, output_config):
        assert len(output_config) == 1
        assert output_config[0]["name"] == "test"
