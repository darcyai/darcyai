FROM edgeworx/darcy-ai-base-x86:dev

RUN python3 -m pip install --upgrade darcyai

COPY src/test.py /src/

ENTRYPOINT ["/bin/bash", "-c", "cd /src/ && python3 -u ./test.py"]