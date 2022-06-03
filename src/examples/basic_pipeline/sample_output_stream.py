#Add the DarcyAI components that we need, particularly the OutputStream
from darcyai.output.output_stream import OutputStream

#Define our own OutputStream class
class SampleOutputStream(OutputStream):
    def __init__(self):
    	#Call init on the parent class
        super().__init__()

    #Define our "write" method for the OutputStream class
    def write(self, data):
        pass

    #Define our "close" method for the OutputStream class
    def close(self):
        pass
