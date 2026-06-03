ARG PYTHON_VERSION=3.13

FROM docker-hosted.artifactory.tcsbank.ru/python/${PYTHON_VERSION}/base/bookworm:latest as builder
LABEL maintainer="Ovsyannikov Roman Dmitrievich ro.ovsyannikov@tbank.ru"

WORKDIR /app

RUN pip install "poetry==2.1.3"

COPY pyproject.toml poetry.lock /app/

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --no-root

FROM docker-hosted.artifactory.tcsbank.ru/python/${PYTHON_VERSION}/base/bookworm:latest as runner

WORKDIR /app

COPY --from=builder /usr/local /usr/local

COPY --from=docker-hosted.artifactory.tcsbank.ru/crat/leader-election:v0.0.15 /leader-election ./leader-election
COPY . .

CMD ./leader-election summarizer uvicorn main:app --host 0.0.0.0 --port 8000
