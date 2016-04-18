#FROM phusion/baseimage:0.9.18
FROM ubuntu:14.04
MAINTAINER PhracturedBlue <deviationtx@gmail.com>
# Use baseimage-docker's init system.
#CMD ["/sbin/my_init"]
CMD ["/root/build.sh"]

RUN apt-get update && apt-get install -y build-essential git libc6-i386 mingw32 mingw32-binutils mingw32-runtime python gettext zip dialog
COPY build.sh /root/
VOLUME /root
VOLUME /git
VOLUME /release


# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
