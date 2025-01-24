# Base image with ARM64 compatibility
FROM python:3.9-slim

# Install system dependencies for dbt
RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install dbt-core and dbt-postgres
RUN pip install --no-cache-dir dbt-core dbt-postgres prefect

# Set the working directory
WORKDIR /usr/app/dbt

# Default command
CMD ["sleep", "infinity"]
