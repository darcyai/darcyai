import os
import platform
import hashlib
import uuid
import analytics
import multiprocessing
import time
import threading

from darcyai.input.input_stream import InputStream

IN_DOCKER_ENV_NAME = 'DARCYAI_IN_DOCKER'
REPORTING_DISABLED_ENV = 'DARCYAI_ANALYTICS_OPTOUT'
WRITE_KEY_ENV = 'DARCYAI_ANALYTICS_WRITE_KEY'
HEARTBEAT_INTERVAL = 10

## Events definition

PIPELINE_BEGIN_EVENT_NAME = 'pipeline_begin'
PIPELINE_END_EVENT_NAME = 'pipeline_end'
PIPELINE_ERROR_EVENT_NAME = 'pipeline_error'
PIPELINE_HEARTBEAT_EVENT_NAME = 'pipeline_heartbeat'

class PipelineBaseEvent():
  def __init__(self,
              machine_id: str,
              pipeline_config_hash: str,
              pipeline_run_uuid: str):
    self.machine_id = machine_id
    self.pipeline_config_hash = pipeline_config_hash
    self.pipeline_run_uuid = pipeline_run_uuid
    return

class PipelineEndEvent(PipelineBaseEvent):
  def __init__(self,
              machine_id: str,
              pipeline_config_hash: str,
              pipeline_run_uuid: str,
              pipeline_config_api_call_count: int):
    super().__init__(machine_id, pipeline_config_hash, pipeline_run_uuid)
    self.timestamp = int(time.time())
    self.pipeline_config_api_call_count = pipeline_config_api_call_count
    return

class PipelineHeartbeatEvent(PipelineBaseEvent):
  def __init__(self,
              machine_id: str,
              pipeline_config_hash: str,
              pipeline_run_uuid: str,
              pipeline_config_api_call_count: int):
    super().__init__(machine_id, pipeline_config_hash, pipeline_run_uuid)
    self.timestamp = int(time.time())
    self.pipeline_config_api_call_count = pipeline_config_api_call_count
    return

class PipelineErrorEvent(PipelineBaseEvent):
  def __init__(self,
              machine_id: str,
              pipeline_config_hash: str,
              pipeline_run_uuid: str,
              error: Exception,
              is_fatal: bool = True):
    super().__init__(machine_id, pipeline_config_hash, pipeline_run_uuid)
    self.exception_message = str(error)
    self.exception_type = str(type(error))
    self.exception_stacktrace = str(error.__traceback__)
    self.timestamp = int(time.time())
    self.is_fatal = is_fatal
    return

class PipelineBeginEvent(PipelineBaseEvent):
  def __init__(self,
              machine_id: str,
              pipeline_config_hash: str,
              pipeline_run_uuid: str,
              os: str,
              os_version: str,
              arch: str,
              containerized: bool,
              using_iofog: bool,
              cpu_count: int,
              google_coral_count: int,
              darcy_ai_engine_version: str,
              python_version: str,
              pipeline_input_stream_count: int,
              pipeline_output_stream_count: int,
              pipeline_perceptor_count: int,
              pipeline_input_stream_names: list[str],
              pipeline_output_stream_names: list[str],
              pipeline_perceptor_names: list[str],
              pipeline_has_parralel_perceptors: bool,
              pipeline_api_call_count: int
              ):
    super().__init__(machine_id, pipeline_config_hash, pipeline_run_uuid)
    self.os = os
    self.os_version = os_version
    self.arch = arch
    self.containerized = containerized
    self.using_iofog = using_iofog
    self.cpu_count = cpu_count
    self.google_coral_count = google_coral_count
    self.darcy_ai_engine_version = darcy_ai_engine_version
    self.python_version = python_version
    self.pipeline_input_stream_count = pipeline_input_stream_count
    self.pipeline_output_stream_count = pipeline_output_stream_count
    self.pipeline_perceptor_count = pipeline_perceptor_count
    self.pipeline_input_stream_names = pipeline_input_stream_names
    self.pipeline_output_stream_names = pipeline_output_stream_names
    self.pipeline_perceptor_names = pipeline_perceptor_names
    self.pipeline_has_parralel_perceptors = pipeline_has_parralel_perceptors
    self.pipeline_api_call_count = pipeline_api_call_count
    return

## Reporter definition

def __get_etc_hostnames():
  """
  Parses /etc/hosts file and returns all the hostnames in a list.
  """
  hosts = []
  if not os.path.exists('/etc/hosts'):
    return hosts
  with open('/etc/hosts', 'r') as f:
      hostlines = f.readlines()
  hostlines = [line.strip() for line in hostlines
                if not line.startswith('#') and line.strip() != '']
  hosts = []
  for line in hostlines:
      hostnames = line.split('#')[0].split()[1:]
      hosts.extend(hostnames)
  return hosts

def __is_using_iofog(self):
  """
  Verifies if iofog is present as an extra host
  """
  hosts = __get_etc_hostnames()
  for host in hosts:
    print(host)
    if host.startswith('iofog'):
      return True
  return False

class AnalyticsReporter():
  """
  The AnalyticsReporter class is Responsible for communicating with the analytics service.

  # Arguments
  darcyai_engine_version (str): the Major.Minor.Patch version of the darcyai engine
  disable_reporting (bool): disable reporting. Defaults to False
  """
  def __init__(self,
               darcyai_engine_version: str,
               disable_reporting: bool = False):
    """
    Checks if reporting is enabled and initialise all constant values.
    """
    self.__reporting_enabled = os.getenv(REPORTING_DISABLED_ENV) != 'True' and not disable_reporting
    if not self.__reporting_enabled:
      return

    write_key = os.getenv(WRITE_KEY_ENV, 'DARnwpKCCqEmYWkyBCGsf7FWWd1HJmHs')
    if write_key is None or write_key == '':
      self.__reporting_enabled = False
      return
    self.__analytics = analytics
    self.__analytics.write_key = write_key
    self.__machine_id = uuid.getnode()
    self.__os_name = platform.system()
    self.__os_version = platform.version()
    self.__os_arch = platform.machine()
    self.__cpu_count = multiprocessing.cpu_count()
    in_docker_env = os.getenv(IN_DOCKER_ENV_NAME)
    self.__containerized = in_docker_env is not None and in_docker_env != ''
    self.__using_iofog = self.__containerized and __is_using_iofog()
    self.__darcyai_engine_version = darcyai_engine_version
    self.__python_version = platform.python_version()

    self.__analytics.on_error = self.__on_analytics_error
    self.__analytics.identify(self.__machine_id)
    self.__pipeline_run_uuid = ''
    return

  def __cancel_heartbeat(self):
    try:
      if self.__heartbeat_tread is not None:
        self.__heartbeat_running = False
        self.__heartbeat_thread.join()
        self.__heartbeat_tread = None
      return
    except AttributeError as e:
      return

  def __on_analytics_error(self, error):
    print('Analytics error: ' + str(error))
    return

  def on_pipeline_begin(self,
                        pipeline_run_uuid: str,
                        pipeline_config_hash: str,
                        google_coral_count: int,
                        pipeline_input_stream_count: int,
                        pipeline_output_stream_count: int,
                        pipeline_perceptor_count: int,
                        pipeline_input_stream_names: list[str],
                        pipeline_output_stream_names: list[str],
                        pipeline_perceptor_names: list[str],
                        pipeline_has_parallel_perceptors: bool,
                        pipeline_api_call_count: int):
    """
    Sends PipelineBeginEvent and start heartbeat.
    """
    if not self.__reporting_enabled:
      return
    self.__pipeline_config_hash = pipeline_config_hash
    self.__pipeline_run_uuid = pipeline_run_uuid
    event = PipelineBeginEvent(self.__machine_id,
                              self.__pipeline_config_hash,
                              self.__pipeline_run_uuid,
                              self.__os_name,
                              self.__os_version,
                              self.__os_arch,
                              self.__containerized,
                              self.__using_iofog,
                              self.__cpu_count,
                              google_coral_count,
                              self.__darcyai_engine_version,
                              self.__python_version,
                              pipeline_input_stream_count,
                              pipeline_output_stream_count,
                              pipeline_perceptor_count,
                              pipeline_input_stream_names,
                              pipeline_output_stream_names,
                              pipeline_perceptor_names,
                              pipeline_has_parallel_perceptors,
                              pipeline_api_call_count)
    self.__analytics.track(self.__machine_id, PIPELINE_BEGIN_EVENT_NAME, vars(event))
    self.__cancel_heartbeat()
    self.__heartbeat_running = True
    self.__heartbeat_tread = threading.Thread(daemon=True, target=self.__run_pipeline_heartbeat)
    self.__heartbeat_tread.start()
    return

  def __run_pipeline_heartbeat(self):
    while self.__heartbeat_running == True:
      self.on_pipeline_heartbeat(0)
      time.sleep(HEARTBEAT_INTERVAL)
    return

  def on_pipeline_heartbeat(self, pipeline_api_call_count: int):
    """
    Sends PipelineHeartbeatEvent
    """
    if not self.__reporting_enabled:
      return
    event = PipelineHeartbeatEvent(self.__machine_id, self.__pipeline_config_hash, self.__pipeline_run_uuid, pipeline_api_call_count)
    self.__analytics.track(self.__machine_id, PIPELINE_HEARTBEAT_EVENT_NAME, vars(event))
    return

  def on_pipeline_end(self, pipeline_api_call_count: int):
    """
    Sends PipelineEndEvent and stops heartbeat.
    """
    if not self.__reporting_enabled:
      return
    event = PipelineEndEvent(self.__machine_id, self.__pipeline_config_hash, self.__pipeline_run_uuid, pipeline_api_call_count)
    self.__analytics.track(self.__machine_id, PIPELINE_END_EVENT_NAME, vars(event))
    self.__cancel_heartbeat()
    return

  def on_pipeline_error(self, error: Exception, is_fatal: bool = True):
    """
    Sends PipelineErrorEvent and stops heartbeat if error is fatal.
    """
    if not self.__reporting_enabled:
      return
    event = PipelineErrorEvent(self.__machine_id, self.__pipeline_config_hash, self.__pipeline_run_uuid, error, is_fatal)
    self.__analytics.track(self.__machine_id, 'pipeline_error', vars(event))
    if is_fatal:
      self.__cancel_heartbeat()
    return

  @staticmethod
  def hash_pipeline_config(input_stream: InputStream, perceptors: dict, perceptor_orders: list[dict], output_streams: dict):
    """
    Returns hash of pipeline config.
    """
    # Basic implementation.
    # Creates a long string, then hashes it.
    # String follows the following format:
    # [typeof(input_stream), typeof(perceptors), typeof(output_streams)].join('')
    # Perceptors are ordered to follow pipeline execution, parallel perceptors are joined with _
    # Output streams are ordered following the dict keys.
    config = [str(type(input_stream))]
    for parralel_perpeptors in perceptor_orders:
      parralel_perpeptors_types = []
      for perceptor_name in parralel_perpeptors:
        parralel_perpeptors_types.append(str(type(perceptors[perceptor_name])))
      config.append('_'.join(parralel_perpeptors_types))
    for output_stream_name in output_streams:
      config.append(str(type(output_streams[output_stream_name].get('stream', None))))

    return hashlib.sha256(''.join(config).encode('utf-8')).hexdigest()