FROM edgeworx/thermal-edge-base:1.0.6

RUN python3 -m pip install darcyai

COPY people_perception.py /src/

ENTRYPOINT ["/bin/bash", "-c", "cd /src/ && python3 ./people_perception.py"]
