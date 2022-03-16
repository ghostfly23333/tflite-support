# Copyright 2022 The TensorFlow Authors. All Rights Reserved.
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
"""A module to record audio in a streaming basis."""
import threading
import numpy as np
import sounddevice as sd


class AudioRecord(object):
  """A class to record audio in a streaming basis."""

  def __init__(
      self, channels: int, sampling_rate: int, buffer_size: int
  ) -> None:
    """Creates an AudioRecord instance.
    Args:
      channels: Number of input channels.
      sampling_rate: Sampling rate in Hertz.
      buffer_size: Size of the ring buffer in number of samples.
    """
    self._audio_buffer = []
    self._buffer_size = buffer_size
    self._channels = channels
    self._sampling_rate = sampling_rate

    # Create a ring buffer to store the input audio.
    self._buffer = np.zeros([buffer_size, channels], dtype=float)
    self._lock = threading.Lock()

    def audio_callback(data, *_):
      """A callback to receive recorded audio data from sounddevice."""
      self._lock.acquire()
      shift = len(data)
      if shift > buffer_size:
        self._buffer = np.copy(data[:buffer_size])
      else:
        self._buffer = np.roll(self._buffer, -shift, axis=0)
        self._buffer[-shift:, :] = np.copy(data)
      self._lock.release()

    # Create an input stream to continuously capture the audio data.
    self._stream = sd.InputStream(
        channels=channels,
        samplerate=sampling_rate,
        callback=audio_callback,
    )

  @property
  def channels(self):
    return self._channels

  @property
  def sampling_rate(self):
    return self._sampling_rate

  @property
  def buffer_size(self):
    return self._buffer_size

  def start_recording(self) -> None:
    """Starts the audio recording."""
    # Clear the internal ring buffer.
    self._buffer.fill(0)

    # Start recording using sounddevice's InputStream.
    self._stream.start()

  def stop(self) -> None:
    """Stops the audio recording."""
    self._stream.stop()

  def read(self, size: int) -> np.ndarray:
    """Reads the latest audio data captured in the buffer.
    Args:
      size: Number of samples to read from the buffer.
    Returns:
      An NumPy array containing the audio data.
    Raises:
      ValueError: Raised if `size` is larger than the buffer size.
    """
    if size > self._buffer_size:
      raise ValueError('Cannot read more samples than the size of the buffer.')

    start_index = self._buffer_size - size
    return np.copy(self._buffer[start_index:])
