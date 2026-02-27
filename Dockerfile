FROM python:3.11-slim

WORKDIR /app

# system deps for cvxpy solvers can be heavy; OSQP/SCS are bundled via pip wheels in most cases.
RUN pip install --no-cache-dir poetry==1.8.3

COPY pyproject.toml README.md /app/
COPY factor_lab /app/factor_lab
COPY configs /app/configs
COPY docs /app/docs
COPY scripts /app/scripts

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["factor-lab", "run", "-c", "configs/demo.yaml"]
