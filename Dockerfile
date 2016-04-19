FROM ubuntu:14.04
MAINTAINER PhracturedBlue <deviationtx@gmail.com>
RUN apt-get update && apt-get install -y build-essential git libc6-i386 mingw32 mingw32-binutils mingw32-runtime gettext zip python python-newt
CMD ["/root/build_init.sh"]

COPY build.py /root/
COPY build_init.sh /root/
RUN sha1sum /root/build.py > /root/.build.py.sha1
VOLUME /root
VOLUME /git
VOLUME /release


# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
