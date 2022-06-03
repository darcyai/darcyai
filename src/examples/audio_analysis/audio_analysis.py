#Add libraries we need
import librosa
import numpy as np
from flask import Flask

#Add the Darcy AI Pipeline object
from darcyai.pipeline import Pipeline

#Add our custom InputStream and Perceptor classes
from audio_input_stream import AudioInputStream
from audio_analysis_perceptor import AudioAnalysisPerceptor

#Define a class to hold our demo application
class AudioAnalyzer():
    def __init__(self):
        #Use our custom audio input stream
        mic = AudioInputStream(sample_len_sec=1)
        self.__rate = mic.get_sample_rate()

        #Create a Darcy AI pipeline with the audio input stream
        self.__pipeline = Pipeline(input_stream=mic)

        #Create an instance of our custom audio analysis percpetor and add it to the pipeline
        audio_perceptor = AudioAnalysisPerceptor()
        self.__pipeline.add_perceptor("audio_analyzer",
                                      audio_perceptor,
                                      input_callback=self.__audio_perceptor_input_callback)

    #Define our "run" method, which is just calling "run" on the pipeline
    def run(self):
        self.__pipeline.run()

    #Define a callback to work with the incoming audio data before it passes into the audio analysis perceptor
    def __audio_perceptor_input_callback(self, input_data, pom, config):
        data = np.frombuffer(input_data.data, dtype=np.float32)
        return data[:193]
        return self.__extract_features(data)

    #Perform audio feature extractions using Numpy that we will pass to the audio analysis AI perceptor
    def __extract_features(self, data):
        features = np.empty((0, 193))

        stft = np.abs(librosa.stft(data))
        mfccs = np.mean(librosa.feature.mfcc(y=data, sr=self.__rate, n_mfcc=40).T, axis=0)
        chroma = np.mean(librosa.feature.chroma_stft(S=stft, sr=self.__rate).T, axis=0)
        mel = np.mean(librosa.feature.melspectrogram(data, sr=self.__rate).T, axis=0)
        contrast = np.mean(librosa.feature.spectral_contrast(S=stft, sr=self.__rate).T, axis=0)
        tonnetz = np.mean(librosa.feature.tonnetz(y=librosa.effects.harmonic(data), sr=self.__rate).T, axis=0)
        ext_features = np.hstack([mfccs, chroma, mel, contrast, tonnetz])
        features = np.vstack([features, ext_features]).astype(np.float32)

        return features

#In the main thread, start the application by instantiating our demo class and calling "run"
if __name__ == "__main__":
    audio_analyzer = AudioAnalyzer()
    audio_analyzer.run()
