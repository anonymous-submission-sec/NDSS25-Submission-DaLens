FROM golang:latest

# Install OpenVPN
RUN apt-get update && apt-get install -y openvpn

# Install curl
RUN apt-get install -y curl

# Install Zdns
#RUN apt-get install -y git
#WORKDIR /
#RUN git clone https://github.com/zmap/zdns.git
#WORKDIR /zdns
#RUN go build
#ENV PATH=${PATH}:/zdns

# Install dnspython
RUN apt install -y python3-dnspython

# Configure VPN credentials
WORKDIR /measurement
RUN echo "vpn\nvpn" > /measurement/creds.txt

# Copy script and set Entry point
COPY engine.py /measurement
ENTRYPOINT ["./engine.py"]
