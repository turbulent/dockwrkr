# dockwrkr
General purpose container composition script.

# Overview

dockwrkr is a simple python script that acts as a wrapper to docker command line arguments.
What dockwrkr adds is the ability for writing PID files of the started containers (for monitoring purposes) as well
as provide a series of simple command to interrogate the docker daemon about container status for your docker containers.

Particularely useful when hooking into upstart and other process manager.

# Usage 

```
Usage: dockwrkr [options] COMMAND [command-options]

Docker container composition (version: 0.3)

Options:
  -f CONFIGFILE  Override default config file
  -d             Activate debugging output
  -y             Assume yes when prompted

Commands:

  help                Print help for a specific command
  create              Create the specified container(s)
  start               Start the specified container(s)
  stop                Stop the specified container(s)
  remove              Remove the specified container(s)
  restart             Stop and Start the specified container(s)
  recreate            Stop, Remove and Start the specified container(s)
  reset               Reset container managed by dockwrkr (stop/remove)
  pull                Pull the specified container(s)
  status              Output the container status table
  exec                Run a command in a running container
  stats               Output live stats for the listed containers
```

## configuration file

dockwrkr will walk up the current directory to locate the file ``dockwrkr.yml``. 

Your YAML configuration file should define a ``containers`` key that lists the run configuration for your containers.

Here is a sample dockwrkr YAML configuration file:

```
pids:
  enabled: True
  dir: pids
containers:
  hello1:
    image: busybox
    hostname: hello1
    env:
      VAR_FOO_VAR: 1
      VAR_FOO_BAR: "string"
      VAR_FOO_VAR: null
    command: /bin/sh -c "while true; do echo hello world; sleep 1; done"
  hello2:
    image: busybox
    hostname: hello1
    env:
      VAR_FOO_VAR: 1
      VAR_FOO_BAR: "string"
      VAR_FOO_VAR: null
    command: /bin/sh -c "while true; do echo hello world; sleep 1; done"
  hello3:
    image: busybox
    hostname: hello1
    env:
      VAR_FOO_VAR: 1
      VAR_FOO_BAR: "string"
      VAR_FOO_VAR: null
    command: /bin/sh -c "while true; do echo hello world; sleep 1; done"
    volume:
      - "/path/to/vol:/dest/of/vol"
```

Each parameter for each container match the ``docker run`` docker client options. 


## pids

dockwrkr can write the pids of the containers it manages. To activate, add the ``pids`` section in your dockwrkr.yml file.

```
pids:
  enabled: true
  dir: path/to/pids
```

If a relative path is specified for ``pids.dir`` , it will be expanded from the configuration file location. 

## status

Returns a table with the PID and UPTIME/EXIT status of the docker-compose services. The program will do the service to container name lookup itself.

Sample output:
```
NAME               CONTAINER      PID      IP             UPTIME               EXIT
web                bdd3de250ecd   3518     172.17.0.19    2 weeks ago          -
sessions           7870988e585d   23520    172.17.0.3     1 months ago         -
db                 71c1407b50d0   23049    172.17.0.1     1 months ago         -
workers            038a169680da   24717    172.17.0.6     1 months ago         -
cache              33934e1a2252   23430    172.17.0.2     1 months ago         -
redis              24e32b1a7f76   23836    172.17.0.4     1 months ago         -
monit              2c997c1b2192   25518    -              1 months ago         -
logrotate          6659049316da   25653    172.17.0.9     1 months ago         -
rabbit             3919187a6b9f   24906    172.17.0.7     1 months ago         -
qmgr               cf6766f0c39c   24364    172.17.0.5     1 months ago         -
cron               45c26cf9c3d4   26279    172.17.0.10    1 months ago         -
```

## start / stop

These commands will start or stop the specified containers. 

```
#host# dockwrkr start web
'web' has been started. 
#host# cat /var/run/docker/dockwrkr/web.pid
18738
#host#
```

You can affect multiple containers at once by listing them on the command line. Alternatively you can also use the -a switch to affect all defined containers.

```
#host# dockwrkr stop web cache
'web' has been stopped.
'cache' has been stopped.
```

```
#host# dockwrkr start -a
'dbmaster' has been created and started.
'cache' has been created and started.
'redis' has been created and started.
'web' has been created and started.
'qmgr' has been created and started.
'cron' has been created and started.
'logrotate' has been created and started.
'abelo' has been created and started.
```

## stats

The program will fetch the running docker containers and launch a "docker stats" stream in your terminal.
```
#host# dockwrkr stats 
CONTAINER           CPU %               MEM USAGE/LIMIT       MEM %               NET I/O
cache               0.00%               1008 KiB/3.614 GiB    0.03%               5.133 KiB/648 B
cron                0.02%               8.629 MiB/3.614 GiB   0.23%               3.043 KiB/648 B
db                  0.11%               210.5 MiB/3.614 GiB   5.69%               18.27 KiB/7.094 KiB
logrotate           0.02%               8.887 MiB/3.614 GiB   0.24%               4.717 KiB/648 B
monit               0.00%               3.637 MiB/3.614 GiB   0.10%               0 B/0 B
qmgr                0.02%               65.94 MiB/3.614 GiB   1.78%               10.21 KiB/13.59 KiB
rabbit              0.68%               87.93 MiB/3.614 GiB   2.38%               12.79 KiB/18.18 KiB
redis               0.04%               7.398 MiB/3.614 GiB   0.20%               4.893 KiB/648 B
sessions            0.00%               1.297 MiB/3.614 GiB   0.04%               5.812 KiB/648 B
web                 0.04%               31.93 MiB/3.614 GiB   0.86%               8.609 KiB/4.31 KiB
workers             0.02%               125.5 MiB/3.614 GiB   3.39%               14.35 KiB/9.502 KiB
```

# exec

Use this command to execute a command within a container.

Example:
```
dockwrkr exec -ti web ps -auxwww
```

```
#host# dockwrkr exec -ti web bash
#container $  exit
#host #
```

# dockwrkr with upstart

Provided you have dockwrkr set up, you will need one upstart job file per service you want to hook. The job will simply instruct dockwrkr to start all it's containers at once.

/etc/init/myservice.conf: 
```
#!upstart
stop on runlevel [06]

chdir /vol
pre-start script
  dockwrkr start -a
end script

post-stop script
  dockwrkr stop -a
end script
```

You can then use *start myservice* and *stop myservice* on your Ubuntu system to control this service.

## Multiple services

You can also use a linked job to start / stop multiple docker containers on host boot / shutdown.
Templating this file with salt/ansible/chef makes this deployment simple for DevOps.

Suppose you have a dockwrkr config file with 3 services : web, db and cache, you could create a master upstart job like so:
```
#!upstart
description     "Host Containers"

start on (filesystem and started docker and net-device-up IFACE!=lo)
stop on runlevel [!2345]

pre-start script
start db || :
start cache || :
start web || :
end script

post-stop script
stop db || :
stop cache || :
stop web || :
end script
```

This would start the *db, cache, web* docker-compose service on host boot.

