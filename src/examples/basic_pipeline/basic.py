#Add the DarcyAI components that we need, particularly the InputStream, OutputStream, Pipeline, and PerceptorMock
from darcyai.tests.perceptor_mock import PerceptorMock
from darcyai.pipeline import Pipeline
from sample_input_stream import SampleInputStream
from sample_output_stream import SampleOutputStream

#Define a class to hold all of our operations
class SingleStreamDemo():
    def __init__(self):
        #Create an input stream and an output stream that we can use in our demo
        ping = SampleInputStream()
        output_stream = SampleOutputStream()

        #Give our class a pipeline property and instantiate it with a Darcy AI pipeline
        self.__pipeline = Pipeline(input_stream=ping,
                                   input_stream_error_handler_callback=self.__input_stream_error_handler_callback,
                                   universal_rest_api=True,
                                   rest_api_base_path="/pipeline",
                                   rest_api_host="0.0.0.0",
                                   rest_api_port=8080)

        #Add our output stream to the pipeline
        self.__pipeline.add_output_stream("output", self.__output_stream_callback, output_stream)

        #Create a mock perceptor and add it to the pipeline
        p1 = PerceptorMock()
        self.__pipeline.add_perceptor("p1", p1, accelerator_idx=0, input_callback=self.__perceptor_input_callback)

    #Define a "run" method that just calls "run" on the pipeline
    def run(self):
        self.__pipeline.run()

    #Define an input callback for the mock perceptor that just sends the data onward with no manipulation
    def __perceptor_input_callback(self, input_data, pom, config):
        return input_data

    #Define an output stream callback that does not manipulate the data
    def __output_stream_callback(self, pom, input_data):
        pass

    #Define an input stream error handler callback that just continues onward
    def __input_stream_error_handler_callback(self, exception):
        pass

#In the main thread, start the application by instantiating our demo class and calling "run"
if __name__ == "__main__":
    single_stream = SingleStreamDemo()
    single_stream.run()