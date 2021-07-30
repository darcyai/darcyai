FROM edgeworx/darcy-ai-sdk-base:1.0.0

RUN python3 -m pip install darcyai==0.1.16

COPY src/examples/static /src/
COPY src/examples/people_perception.py /src/demo.py

ENTRYPOINT ["/bin/bash", "-c", "cd /src/ && python3 ./demo.py"]
