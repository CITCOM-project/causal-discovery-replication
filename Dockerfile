FROM python:3.12-bookworm

RUN addgroup --gid 1002 "experimental" && \
    adduser --disabled-password --gecos "Experimental User,,," \
    --home /home/experimental --ingroup experimental --uid 1002 experimental

# Set working directory
WORKDIR /home/experimental

RUN apt update; apt install -y r-base

USER 1002:1002


# Clone the repo and set up config with dummy details
RUN git clone https://github.com/CITCOM-project/causal-discovery-replication.git

WORKDIR /home/experimental/causal-discovery-replication

RUN git checkout jmafoster1/new-results; \
  chmod +x src/run_synthetic_discovery.sh; \
  pip install .
COPY --chown=1002:1002 src/setup.r setup.r
RUN Rscript setup.r

ENTRYPOINT ["/bin/bash", "src/run_synthetic_discovery.sh"]
