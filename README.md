# PunkVision

A realtime vision program for FRC teams.

## Installing

### Deploying

Run `./scripts/deploy.sh` to deploy to `pi@raspberrypi.local:~/` (you have to be connected to the same network).

You'll have to enter the same password twice (for raspberrypis, the default password is `raspberry`)

### Autostart script

Now, ssh to raspberry pi `ssh pi@raspberrypi.local`.

To get an autostarting program to run repeatedly, add a file `/etc/rc.local` on the coprocessor (if it doesn't exist), and make sure it is executable `chmod +x /etc/rc.local`. Then, add the following line: `sh /home/pi/punkvision/scripts/autostart.sh &`.

**IMPORTANT** Make sure the file ends with `exit 0`, and that there is no `exit 0` before our script execution. This will exit the script, and not execute your file! Also, make sure this doesn't hang or exit nonzero. This will mess up the boot!

### Configuring networking for competition

At the end of `/etc/dhcpcd.conf`, take the following text and replace TE.AM with your team number, and replace RPI with the last number (no .), so it may look like: `static ip_address=10.39.66.176/24`, and you can connect to the raspberry pi at `raspberrypi.local` or `10.39.66.176`.

``` bash
#... SOME RANDOM STUFF

interface eth0

static ip_address=10.TE.AM.RPI/24
static routers=10.TE.AM.1
static domain_name_servers=10.TE.AM.1
```


## TODO

  + Use [cscore](http://robotpy.readthedocs.io/en/stable/vision/other.html) for streaming to the driver station (right now, you have to open a web browser)
  + Add documentation, and a formal LaTeX paper
  + Provide raspi images for teams to use
  + Add Makefile to install correct packages, and detect some things (probably not enough to warrant a ./configure step)


## BUGS

Please report bugs to the [issues](https://github.com/LN-STEMpunks/PunkVision/issues)


## TESTS

Some could be hard to implement (because it needs to be ran live most of the time), and every camera is different.

