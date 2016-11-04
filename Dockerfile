FROM devopsftw/baseimage
MAINTAINER Alex Salt <alex.salt@e96.ru>

ENV DEBIAN_FRONTEND noninteractive

# install percona xtradb cluster
RUN curl -sL https://repo.percona.com/apt/percona-release_0.1-4.$(lsb_release -sc)_all.deb -o /tmp/percona-release.deb && \
    dpkg -i /tmp/percona-release.deb && \
    apt-get update -qq && \
    apt-get -y --no-install-recommends install \
    qpress percona-xtradb-cluster-56

# install galera-healthcheck
RUN curl -sL https://github.com/sttts/galera-healthcheck/releases/download/v20150303/galera-healthcheck_linux_amd64 -o /bin/galera-healthcheck && \
    test "$(sha256sum /bin/galera-healthcheck | awk '{print $1;}')" = "86f60d9d82b1f9d2d474368ed7e81a0a361508031a292244847136b0ed2ee770" && \
    chmod +x /bin/galera-healthcheck

# python
RUN apt-get install -y python3-setuptools && \
    easy_install3 pip

RUN rm -rf /etc/my.cnf /etc/mysql/my.cnf
COPY my.cnf /etc/mysql/my.cnf
RUN chown mysql.mysql /etc/mysql/my.cnf

COPY start /start
RUN chmod 555 /start

COPY service.json /etc/consul/conf.d/

# election service
ENV CLUSTER_NAME cluster
COPY elect /elect
RUN pip install -r /elect/requirements.txt && \
    mkdir /etc/service/elect && \
    ln -sv /elect/elect.py /etc/service/elect/run

# cleanup
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 3306 4444 4567 4568
VOLUME ["/var/lib/mysql"]

ENTRYPOINT [ "/sbin/my_init", "/start" ]
