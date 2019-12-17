FROM nbcc/centos7-slurm

# ---- setup user and home dir
RUN cp -r /etc/skel /home/nbcc \
    && groupadd -r --gid=1000 nbcc \
    && useradd -r -g nbcc --uid=1000 -d /home/nbcc nbcc \
    && mkdir -p /home/nbcc/www/prowave \
    && chown nbcc:nbcc -R /home/nbcc

RUN yum install -y https://centos7.iuscommunity.org/ius-release.rpm \
    && yum update -y \
    && yum install -y python36u python36u-libs python36u-devel python36u-setuptools \
    && unlink /bin/python \
    && unlink /bin/pip \
    && ln -s /bin/python3.6 /bin/python \
    && ln -s /bin/pip3.6 /bin/pip

RUN pip install Cython

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY docker-entrypoint.sh /docker-entrypoint.sh

USER nbcc
# ---- environment variables
ENV PATH /opt/apps/slurm/bin:$PATH

USER root

VOLUME [ "/home/nbcc/www", "/data" ]

ENTRYPOINT [ "/usr/local/bin/tini", "--", "/docker-entrypoint.sh" ]
CMD [ "/bin/bash" ]
