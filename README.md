WHAT IS THAT?
=============
This is Percona Cluster docker image with consul agent and leader election

ENV VARS YOU SHOULD KNOW OF
---------------------------
* CONSUL_HOST (ip address of consul cluster to join to, defaults to gateway)
* CLUSTER_NAME (name of cluster, will register as clustername
and clustername-leader service)
* XTRABACKUP_PASSWORD (password for xtrabackup user for SST)
* MYSQL_ROOT_PASSWORD (mysql root password, used on bootstrapping)

HOW TO USE
----------
```
# docker pull devopsftw/pxc
# docker run \
    -e XTRABACKUP_PASSWORD=12345 \
    -e CLUSTER_NAME=pxc \
    -d devopsftw/pxc \
    seed -- --innodb-buffer-pool-size=10g
# docker run \
    -e XTRABACKUP_PASSWORD=12345 \
    -e CLUSTER_NAME=pxc \
    -d devopsftw/pxc \
    node node-ip-here -- --innodb-buffer-pool-size=10g
```
