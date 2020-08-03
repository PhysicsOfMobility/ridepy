FROM gitpod/workspace-full

# Install custom tools, runtime, etc.
RUN sudo apt-get update && apt-get install -y libcr-dev mpich2 mpich2-doc