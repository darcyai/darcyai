import collections
import math

import numpy as np
from pkg_resources import parse_version
from edgetpu import __version__ as edgetpu_version

from edgetpu.detection.engine import DetectionEngine
from edgetpu.utils import image_processing
from PIL import Image

class ObjectDetectionEngine(DetectionEngine):
  """Engine used for object detections."""

  def __init__(self, model_path, device_path=None):
    """Creates an ObjectDetectionEngine with given model.

    Args:
      model_path: String, path to TF-Lite Flatbuffer file.

    Raises:
      ValueError: An error occurred when model output is invalid.
    """
    DetectionEngine.__init__(self, model_path, device_path)

    self._input_tensor_shape = self.get_input_tensor_shape()
    if (self._input_tensor_shape.size != 4 or
            self._input_tensor_shape[3] != 3 or
            self._input_tensor_shape[0] != 1):
      raise ValueError(
          ('Image model should have input shape [1, height, width, 3]!'
            ' This model has {}.'.format(self._input_tensor_shape)))
    _, self.image_height, self.image_width, self.image_depth = self.get_input_tensor_shape()

    # The API returns all the output tensors flattened and concatenated. We
    # have to figure out the boundaries from the tensor shapes & sizes.
    offset = 0
    self._output_offsets = [0]
    for size in self.get_all_output_tensors_sizes():
      offset += size
      self._output_offsets.append(int(offset))

  def DetectObjectInImage(self, img):
    """Detects object in a given image.

    Args:
      img: numpy array containing image
    """

    # Extend or crop the input to match the input shape of the network.
    if img.shape[0] < self.image_height or img.shape[1] < self.image_width:
      img = np.pad(img, [[0, max(0, self.image_height - img.shape[0])],
                          [0, max(0, self.image_width - img.shape[1])], [0, 0]],
                    mode='constant')
    img = img[0:self.image_height, 0:self.image_width]
    print("Image Shape: {}".format(img.shape))
    print("Tensor Shape: {}".format(tuple(self._input_tensor_shape[1:])))
    assert (img.shape == tuple(self._input_tensor_shape[1:]))

    # Run the inference (API expects the data to be flattened)
    objs = self.detect_with_input_tensor(img.flatten(),
                                  threshold=0.05,
                                  top_k=10)

    return self.ParseOutput(objs)

  def ParseOutput(self, output):
    inference_time, _ = output
    return output, inference_time
