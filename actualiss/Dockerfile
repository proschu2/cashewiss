FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml README.md .
RUN pip install --no-cache-dir -e .[gui]

# Copy application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD streamlit health actualiss/streamlit/app.py || exit 1

# Run Streamlit
CMD ["streamlit", "run", "actualiss/streamlit/app.py", "--server.port=8501", "--server.address=0.0.0.0"]