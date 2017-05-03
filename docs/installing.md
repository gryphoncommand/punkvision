
# Installing

## Platforms

  * MacOS
  * Linux (Ubuntu/Kali)
  * Windows (not supported yet)

## Embedded

Some embedded platforms are also being used.

  * raspberry PI (raspbian)
  * roboRIO (not yet)



# How to

## Raspberry PI

This is probably the most common use case, so here is a quick example of how to install it on a raspberry pi.

 1. Get a raspberry PI with raspbian on it. We recommend and use raspberry PI 3 s, due to their speed. This computer will be called `TARGET` throughout the tutorial.
 2. Download a [release](https://github.com/lnstempunks/PunkVision/releases) (or [clone](https://github.com/lnstempunks/PunkVision) the latest) on a developer machine. This computer will be called `HOST` throughout the tutorial.
 3. Copy this over to the raspberry pi. Run `./scripts/deploy.sh` to do this for you.
 4. Install on the raspberry PI. ssh to the raspberry pi (run something like `ssh pi@raspberrypi.local`), run `cd ~/`, and then `tar xfv ~/Downloads/punkvision.tar.xz`. This should create a folder `~/punkvision`.
 5. Install required software. Run `sudo ./scripts/install_raspi.sh` to install all software. This needs an internet connection, and will take about an hour or so.
 6. Now, create autoscripts. These are all in the form `scripts/auto_$X.sh`, creating as many as you'd like (that start with `auto_`). You can copy `auto_nothing.sh` to get started.
 7. After some tweaking, run `sudo ./scripts/update_raspi.sh` which should update the `/etc/rc.local` file to include all autoscripts.

You should have it!

