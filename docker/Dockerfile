FROM python:3.12

WORKDIR /app

# Install poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# Install necessary packages
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# Copy the script
COPY --chmod=700 . .

# # Make the script executable
RUN poetry install

# Set as entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Default command (will show help)
CMD ["--help"]