FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV GROQ_API_KEY=""

# system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# set working directory
WORKDIR /app

# copy project files
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY schema.json .
COPY llm_planner.py .
COPY validator.py .
COPY executor.py .
COPY main.py .

CMD ["python3", "main.py"]
