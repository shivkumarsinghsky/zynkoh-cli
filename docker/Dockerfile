# zynkoh-cli as a container: generates code into the mounted /work directory.
# Build: docker build -f docker/Dockerfile -t zynkoh-cli .
# Run:   docker run --rm -u "$(id -u):$(id -g)" -v "$PWD":/work zynkoh-cli create module eam

FROM python:3.12-slim AS build
WORKDIR /src
RUN pip install --no-cache-dir build
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m build --wheel --outdir /dist

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=build /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl \
    && useradd --create-home --uid 10001 zynkoh
USER zynkoh
WORKDIR /work
ENTRYPOINT ["zynkoh"]
CMD ["--help"]
