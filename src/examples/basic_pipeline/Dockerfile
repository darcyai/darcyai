FROM darcyai/darcy-ai-base:dev


WORKDIR /src

RUN python3 -m pip install darcyai --upgrade

COPY . /src/

CMD python3 -u basic.py