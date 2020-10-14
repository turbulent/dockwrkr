# dockwrkr

General purpose container composition script.

## Overview

`dockwrkr` is a simple python script that acts as a wrapper to Docker command
line arguments. What `dockwrkr` adds is the ability for writing PID files of
the started containers (for monitoring purposes) as well as provide a series
of simple command to interrogate the Docker daemon about container status for
your Docker containers.

Particularly useful when hooking into systemd, Upstart, or other process
managers.

## Why not use `docker-compose`?

This script is similar to `docker-compose`, except that it invokes the actual
`docker run` command-line options directly. If a new version of Docker adds
a new option to `docker run`, you don't need to upgrade this script, you can
start using the option right away in your `dockwrkr.yml` file!

## Requirements

This script requires Python 2.7.x to work. Support for Python 3.x is not ready
yet.

The `docker` command-line tool must also be in your `PATH` variable for this
script to work properly.

## Usage

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
  login               Perform docker login using credentials in dockwrkr.yml
  run                 Run the specified job container
```

### Configuration File

`dockwrkr` will walk up the current directory to locate the file
``dockwrkr.yml``.

Your YAML configuration file should define a `containers` key that lists the
run configuration for your containers.

Here is a sample `dockwrkr.yml` configuration file:

```
pids:
  enabled: True
  dir: pids
services:
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
jobs:
  print-foo-variables:
    image: busybox
    env:
      VAR_FOO_VAR: 1
      VAR_FOO_BAR: "string"
      VAR_FOO_VAR: null
    command: ['/bin/sh', '-c', 'env | grep FOO']
    volume:
      - "/path/to/vol:/dest/of/vol"
```

Each parameter for each container definition (in `services` or `jobs`) match
the ``docker run`` Docker client [options](https://docs.docker.com/engine/reference/run/#overriding-dockerfile-image-defaults).


### PIDs

`dockwrkr` can write the pids of the services it manages. To activate, add the
``pids`` section in your `dockwrkr.yml` file.

```
pids:
  enabled: true
  dir: path/to/pids
```

If a relative path is specified for `pids.dir`, it will be expanded from the
configuration file location.

### status

Returns a table with the PID and UPTIME/EXIT status of the services. The
program will do the service-to-container name lookup itself.

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

### start / stop

These commands will start or stop the specified containers.

```
# dockwrkr start web
'web' has been started.
# cat /var/run/docker/dockwrkr/web.pid
18738
```

You can affect multiple containers at once by listing them on the command line.
Alternatively you can also use the `-a` switch to affect all defined
containers.

```
# dockwrkr stop web cache
'web' has been stopped.
'cache' has been stopped.
```

```
# dockwrkr start -a
'dbmaster' has been created and started.
'cache' has been created and started.
'redis' has been created and started.
'web' has been created and started.
'qmgr' has been created and started.
'cron' has been created and started.
'logrotate' has been created and started.
'abelo' has been created and started.
```

#### Extra start flags

Additional flags can be added to the docker `start` command by using the `extra-flags` configuration key.

```
services:
  hello1:
    image: busybox
    hostname: hello1
    extra-flags:
      - "--interactive"
```

See `docker start --help` for additional options.

### stats

The program will fetch the running Docker containers and launch a "docker
stats" stream in your terminal.

```
# dockwrkr stats
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

### exec

Use this command to execute a command within a service container.

Example:
```
dockwrkr exec -ti web ps -auxwww
```

```
host # dockwrkr exec -ti web bash
web $  exit
host #
```

### run

Use this command to execute a jobs defined in the `jobs` section of
`dockwrkr.yml`.

Using the example configuration, you can execute the `print-foo-variables` job like so:

```
host # dockwrkr run print-foo-variables
```

You can pass additional parameters to the command; there will be appended to
the command defined in the job.

## Logging into docker registries

If you want `dockwrkr` to automatically login to your private registry you can
supply credentials for it in your `dockwrkr.yml` file. If `dockwrkr` tries to
pull an image from a registry that is defined in the `registries` configuration
key, it will attempt to automatically login before pulling.

You can also manually login via the command `dockwrkr login`.

Here's an example of a simple registry definition in `dockwrkr.yml`:

```
pids:
  enabled: True
  dir: pids
registries:
  myregistry.com:
    username: foo
    password: bar
    email: foo@bar.com
services:
  private:
    image: rmyregistry.com/path/private_image:0.4
    hostname: private
```

This works well with Amazon's Elastic Container Registry (ECR):

```
pids:
  enabled: True
  dir: pids
registries:
  848559394958.dkr.ecr.us-east-1.amazonaws.com:
    username: AWS
    password: |
        CiBwm0YaIyYjCVV+BAIBEICCAoo55cBYr9IBaPchhO8Ba0iPy8xRFuvIOSaw2yHVV/lE1
        v5e9FZGck03lrA7q/rAFHRjvCrOdSS+/cvV2kpFv1drVEiMR9EEDRKdgLEw4ung3YrKDHqVZjXhxWaRiC2mFIKaDFNjyNYxY6Kmg5JCJTCwHRjOoWADJ0SJRDJdcqN8oKkyUvCEgW8idIWsFw5pjCLtQNtI2VX3XrnE8s5GLddQIsJOG3d1ak3a8LFzXUVb+V3eOysAuLtrCcZlPGyODZHI1nfcgcqjh16zeNitqRI2+H8G+kGAL2Xlbzwp8gVNkH+AX/vkbi0/1QFy/8KgyC7jvnn3+gedXqjNSW4sDS0yjCyp6pL+S4MVTkyq8fkrB/tdgRtJm5n1G6uqeekXuoXXPe5UFce9Rq8/14xKABgEBAgB4cJtGGiEiXkbSZuZ9RurqnnpF7qF1z3uVBXHvUavP9eMAAAL        XMIIC0wYsXHix4VRzWyzUbB8PANn/Qojf1oMQkQ2u15CZJ8Tol0LHgDi5/qGZ+wHTn+sz/dilpwlmrTuo+6avfZdfQy9r47+EPohNB0OquH03gt3fSjR5efU0ldE62VL/GrgHpgOH9qfSsCDvnKDuwfD5lFEIc3npcLh3djbcchTzCSqHdjAjgQgMQh54JSojL3TydS8WclKg6/W7wQIaozk+zfOoETPq90nO1UtT9QbBxbBBqL1JOs9Wu1owX1Ec9wS5oIuwXYNpHqDTA0EQTV4jZsZ335JMAijcM5GHN7MJ2ukOXOffonmHKoVdNJ7RpLBdz8moVKewhOF4jSh8GMbWu19W3uJsGHyS1oMfZz17whuWdetF77cf5cSUF7HXJEW77zDGRUVo0PWqg2CNEdCaonasScWKLQcT1AjhrQ+ctiXZcjoZGRRxFIZ8qR6t3lwn+sZIGszRkdhEI3lKW7EfZl4PfJVieip8m4sccbcetUzjLeSJeJKoZIhvcNAQcGoIICxDCCAsACAQAwggK5BgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDGyzVF8QSt9pZg9PIg==
    email: "none"
services:
  private:
    image: 848559394958.dkr.ecr.us-east-1.amazonaws.com/path/private_image:0.4
    hostname: private
```

# Creating user defined networks
If you want to create user defined networks, you can define them in your
dockwrkr.yml file.

```
pids:
  enabled: True
  dir: pids
registries:
  myregistry.com:
    username: foo
    password: bar
    email: foo@bar.com
networks:
  container-network:
    driver: bridge
    subnet: 172.19.0.0/16

```

And then specify them in your container definition. You can also optionally
assign it a static IP
```
services:
  private:
    image: rmyregistry.com/path/private_image:0.4
    hostname: private
    net: container-network
    ip: 172.19.0.11
```

# dockwrkr with upstart

Provided you have dockwrkr set up, you will need one upstart job file per
service you want to hook. The job will simply instruct dockwrkr to start all
it's containers at once.

/etc/init/myservice.conf:

Provided you have `dockwrkr` set up, you will need one upstart job file per
service you want to hook. The job will simply instruct `dockwrkr` to start all
its containers at once.

`/etc/init/myservice.conf`:
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

You can then use *start myservice* and *stop myservice* on your Ubuntu system
to control this service.

### Multiple services

You can also use a linked job to start / stop multiple Docker containers on
host boot / shutdown. Templating this file with salt/ansible/chef makes this
deployment simple for DevOps.

Suppose you have a `dockwrkr.yml` file with 3 services : web, db and cache, you
could create a master upstart job like so:

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

## License

All work found under this repository is licensed under the [Apache
License 2.0](LICENSE).

