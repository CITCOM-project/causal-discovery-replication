FROM python:3.12-bookworm

RUN addgroup --gid 1002 "experimental" && \
    adduser --disabled-password --gecos "Experimental User,,," \
    --home /home/experimental --ingroup experimental --uid 1002 experimental

# Set working directory
WORKDIR /home/experimental

RUN apt update; apt install -y r-base

USER 1002:1002

# Clone the repo and set up config with dummy details
COPY --chown=1002:1002 src src
COPY --chown=1002:1002 pyproject.toml pyproject.toml

RUN chmod +x src/run_synthetic_discovery.sh; \
  Rscript src/setup.r; \
  pip install .

ENTRYPOINT ["/bin/bash", "src/run_synthetic_discovery.sh"]
