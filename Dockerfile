FROM nbcc/centos7-slurm

# ---- setup user and home dir
RUN cp -r /etc/skel /home/nbcc \
    && groupadd -r --gid=1000 nbcc \
    && useradd -r -g nbcc --uid=1000 -d /home/nbcc nbcc \
    && mkdir -p /home/nbcc/www/prowave \
    && chown nbcc:nbcc -R /home/nbcc

COPY ./requirements.txt /requirements.txt

RUN set -ex \
  && yum install -y python-pip python-virtualenv

RUN set -ex \ 
  && yum install -y https://centos7.iuscommunity.org/ius-release.rpm \
  && yum install -y python36u python36u-libs python36u-devel python36u-pip \
  && yum clean all \
  && rm -rf /var/cache/yum

USER nbcc
WORKDIR /home/nbcc
RUN set -ex \
  && virtualenv -p python3.6 venv \
  && source venv/bin/activate \
  && pip install --upgrade pip \
  && pip install Cython \
  && pip install -r /requirements.txt

# ---- environment variables
ENV PATH /home/nbcc/venv/bin:/opt/apps/slurm/bin:$PATH

USER root
COPY controller-entrypoint.sh /docker-entrypoint.sh

VOLUME [ "/home/nbcc/www", "/data" ]
CMD [ "/bin/bash" ]
