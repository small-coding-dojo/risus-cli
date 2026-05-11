FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[server]"

COPY server/ ./server/

# TODO: Finding: Concepts and technologies used are not explained. We need to consider that the code readers are "python beginners".
#
# Here: What is uvicorn? How is it used? What does it do?
# https://uvicorn.dev/
# Uvicorn runs the file ./server/app.py, which contains the FastAPI app.
#
# What happens if the ping timeout is reached?
# Why shouldn't the timeout be shorter?
# Why do we keep the default for the interval and deviate from the default for the timeout?

# TODO: Finding: Since we already give the default value for --ws-ping-interval, why don't
#
# we also give the default values for all other uvicorn options?
# (there are 18 "default" values for uvicorn options)
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8765", "--ws-ping-interval", "20", "--ws-ping-timeout", "10"]
