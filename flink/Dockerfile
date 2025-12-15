FROM apache/flink:1.17.1

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3 /usr/bin/python

# JAR 파일 복사
COPY lib/*.jar /opt/flink/lib/

WORKDIR /opt/flink/usrlib

COPY requirements.txt .
RUN pip3 install -r requirements.txt