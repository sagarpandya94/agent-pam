FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    openssh-server \
    curl \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Create ubuntu user
RUN useradd -m -s /bin/bash ubuntu && \
    echo "ubuntu:ubuntu123" | chpasswd

# SSH config — allow password auth for local dev
RUN mkdir /var/run/sshd && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config

# Pre-load realistic test data
COPY setup.sh /setup.sh
RUN chmod +x /setup.sh && /setup.sh

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
