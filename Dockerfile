FROM krallin/centos-tini:7

# ----- setup slurm workload manager
ARG SLURM_TAG=slurm-18-08-6-2
ARG GOSU_VERSION=1.11

RUN set -ex \
    && yum makecache fast \
    && yum -y update \
    && yum -y install epel-release \
    && yum -y install \
       wget \
       bzip2 \
       perl \
       gcc \
       gcc-c++\
       git \
       gnupg \
       make \
       munge \
       munge-devel \
       python-devel \
       python-pip \
       python34 \
       python34-devel \
       python34-pip \
       mariadb-server \
       mariadb-devel \
       psmisc \
       bash-completion \
       vim-enhanced \
    && yum clean all \
    && rm -rf /var/cache/yum

RUN pip install Cython nose && pip3.4 install Cython nose

RUN set -ex \
    && wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-amd64" \
    && wget -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-amd64.asc" \
    && export GNUPGHOME="$(mktemp -d)" \
    && gpg --keyserver ha.pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 \
    && gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu \
    && rm -rf "${GNUPGHOME}" /usr/local/bin/gosu.asc \
    && chmod +x /usr/local/bin/gosu \
    && gosu nobody true

RUN set -x \
    && git clone https://github.com/SchedMD/slurm.git \
    && pushd slurm \
    && git checkout tags/$SLURM_TAG \
    && ./configure --enable-debug --prefix=/opt/apps/slurm --sysconfdir=/etc/slurm \
        --with-mysql_config=/usr/bin  --libdir=/usr/lib64 \
    && make install \
    && popd \
    && rm -rf slurm \
    && groupadd -r --gid=990 slurm \
    && useradd -r -g slurm --uid=990 slurm \
    && chown -R slurm:slurm /opt/apps/slurm \
    && mkdir -p /etc/slurm \
    && mkdir -p /etc/munge

COPY _artifacts_/munge.key /etc/munge/
RUN chmod 700 /etc/munge/munge.key && chown munge:munge /etc/munge/munge.key

# ---- setup user and home dir
RUN cp -r /etc/skel /home/nbcc \
    && groupadd -r --gid=1000 nbcc \
    && useradd -r -g nbcc --uid=1000 -d /home/nbcc nbcc \
    && mkdir -p /home/nbcc/www/prowave \
    && chown nbcc:nbcc -R /home/nbcc

USER nbcc
# ---- environment variables
ENV PATH /home/nbcc/anaconda3/bin:/opt/apps/slurm/bin:$PATH

# ---- setup miniconda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh \
    && /bin/bash ~/miniconda.sh -b -p /home/nbcc/anaconda3 \
    && rm ~/miniconda.sh \
    && conda init \
    && conda clean -afy

COPY ./requirements.txt /home/nbcc/requirements.txt
RUN pip install -r /home/nbcc/requirements.txt

USER root
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN set -x \
    && mkdir -p /var/spool/slurm/slurm.state \
    && chown slurm:slurm /var/spool/slurm/slurm.state

VOLUME [ "/home/nbcc/www", "/data" ]

ENTRYPOINT [ "/usr/local/bin/tini", "--", "/docker-entrypoint.sh" ]
CMD [ "/bin/bash" ]
