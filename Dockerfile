FROM python:3.9-slim-buster as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app


FROM base as builder

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN apt update \
    && apt install --no-install-recommends -y \
    curl \
    build-essential

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
ENV PATH="/root/.poetry/bin:$PATH"

COPY poetry.lock pyproject.toml ./
RUN poetry export -o requirements.txt \
    && pip install --user -r requirements.txt


FROM base as production

COPY --from=builder /root/.local /root/.local
COPY swissmetnet ./swissmetnet

ENTRYPOINT ["python", "-m", "swissmetnet.main"]
