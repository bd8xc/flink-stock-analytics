FROM flink:1.18.1

# Install Python, Java, curl, and other dependencies
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip python3-dev openjdk-21-jdk ant curl && \
    rm -rf /var/lib/apt/lists/*

# Ensure python command points to python3
RUN ln -s /usr/bin/python3 /usr/bin/python

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-arm64

WORKDIR /opt/flink
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY download_libs.sh .
RUN chmod +x ./download_libs.sh && ./download_libs.sh

COPY ./usr_jobs/ ./usr_jobs