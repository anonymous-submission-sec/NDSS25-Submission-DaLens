#! /bin/bash

# Instructions from https://github.com/idealeer/xmap/blob/master/INSTALL.md

# Install dependencies
sudo apt-get install -y build-essential cmake libgmp3-dev gengetopt libpcap-dev flex byacc libjson-c-dev pkg-config libunistring-dev

# Install utilities
apt install -y unzip

# Clone XMap repository
wget https://github.com/idealeer/xmap/releases/download/2.0.0/xmap-2.0.0.zip
unzip xmap-2.0.0.zip
cd xmap-2.0.0

# Install XMap
cmake -DENABLE_DEVELOPMENT=OFF -DENABLE_LOG_TRACE=OFF .
make -j 4
make install