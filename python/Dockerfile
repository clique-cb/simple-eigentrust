# build stage
FROM python:3.10 AS builder

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm

# copy files
COPY pyproject.toml pdm.lock README.md /project/
COPY src/ /project/src

# install dependencies and project into the local packages directory
WORKDIR /project
RUN mkdir __pypackages__ && pdm sync --prod --no-editable


# run stage
FROM python:3.10 as sim-server

ARG PORT

# retrieve packages from build stage
ENV PYTHONPATH=/project/pkgs
COPY --from=builder /project/__pypackages__/3.8/lib /project/pkgs

# retrieve executables
COPY --from=builder /project/__pypackages__/3.8/bin/* /bin/

# set command/entrypoint, adapt to fit your needs
CMD ["clique-sim-server", "--port", "${PORT}"]