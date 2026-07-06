FROM langflowai/langflow:latest

USER root

# Install system dependencies for Docling
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0

# Install Langflow with pymysql extra
RUN uv pip install pymysql

# Install Langflow with Docling extra
RUN uv pip install 'langflow[docling]' lfx-docling

# Install Langflow with Docling extraffmpeg to process video input (mp4)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Switch back to Langflow's default user
USER 1000





