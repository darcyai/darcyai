from darcyai.tests.perceptor_mock import PerceptorMock
from darcyai.pipeline import Pipeline
from sample_output_stream import SampleOutputStream
from sample_input_stream import SampleInputStream

def perceptor_input_callback(input_data, pom, config):
    return input_data


def output_stream_callback(pom, input_data):
    pass


input_stream = SampleInputStream(max_runs=2)
output_stream = SampleOutputStream()

pipeline = Pipeline(input_stream)

pipeline.add_output_stream("output", output_stream_callback, output_stream)

p1 = PerceptorMock()
pipeline.add_perceptor("p1", p1, accelerator_idx=0, input_callback=perceptor_input_callback)

pipeline.run()
