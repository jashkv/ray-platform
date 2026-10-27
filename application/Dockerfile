# ==============================================================================
# Production Ray Application Container
# Base: rayproject/ray:2.40.0-py311 (Official CPU base)
# ==============================================================================
FROM rayproject/ray:2.40.0-py311

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app" \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Switch to root temporarily only for system packages if needed
USER root

# Clean up any potential apt caches to reduce image surface
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Switch back to non-root ray user (UID 1000)
USER ray

# Copy pinned requirements first for layer caching
COPY --chown=ray:ray application/requirements.txt /app/requirements.txt

# Install application dependencies
RUN pip install --no-cache-dir --user -r /app/requirements.txt

# Copy application source code, configurations, and reference data
COPY --chown=ray:ray application/ /app/application/
COPY --chown=ray:ray pyproject.toml /app/pyproject.toml

# Container healthcheck verifying runtime dependency integrity
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 -c "import ray, pyiceberg, xgboost, sklearn, pandas, pyarrow; print('healthcheck: OK')" || exit 1

# Default entrypoint for RayJob execution
ENTRYPOINT ["python3", "-m", "application.src.ray_pipeline"]
CMD ["--s1-input", "/app/application/data/supply_chain_data_s1.csv", "--s2-input", "/app/application/data/financial_data_s2.csv"]
