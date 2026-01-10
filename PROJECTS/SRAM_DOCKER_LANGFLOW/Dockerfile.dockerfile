FROM langflowai/langflow:latest

USER root

# Install system dependencies for Docling
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0

# Install Langflow with Docling extra
RUN uv pip install 'langflow[docling]'