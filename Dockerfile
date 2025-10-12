FROM python:3.11-slim

WORKDIR /app

# Copy package files
COPY pyproject.toml MANIFEST.in README.md LICENSE ./
COPY invokeai_mcp_server.py ./

# Install the package
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Run the MCP server
CMD ["python", "-m", "invokeai_mcp_server"]
