
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

NOTE: This is for a coprocessor raspberrypi and will change network settings. If there is an error connecting to the raspi after this, run `sudo cp /etc/dhcpcd.conf.OLD /etc/dhcpcd.conf`, and open an issue on github.

 1. Get a raspberry PI with raspbian on it. We recommend and use raspberry PI 3 s, due to their speed. This computer will be called `TARGET` throughout the tutorial.
 2. Download a [release](https://github.com/lnstempunks/PunkVision/releases) (or [clone](https://github.com/lnstempunks/PunkVision) the latest) on a developer machine. This computer will be called `HOST` throughout the tutorial.
 3. Edit configuration files `./TE.AM` and `./R.PI`. `TE.AM` should include the middle part of the IP for your team. For example, if your team name is `ABCD`, `./TE.AM` should include `AB.CD`. If your team name is only 3 digits (`ABC`), `./TE.AM` should include `A.BC`, or for double digit teams, should include `0.AB` (I think!). `./R.PI` should be the last bit of the static IP for the raspberry pi. So, if your team name is `ABCD`, and you want to connect to the raspi at `10.AB.CD.176`, `./R.PI` should only contain `176`.
 4. Copy this over to the raspberry pi. Run `./scripts/deploy.sh` to do this for you.
 5. Install on the target. ssh to the raspberry pi (run something like `ssh pi@raspberrypi.local`), run `cd ~/`, and then `tar xfv ~/Downloads/punkvision.tar.xz`. This should create a folder `~/punkvision`.
 6. Install required software. Run `sudo ./scripts/install_raspi.sh` on the target to install all software. This needs an internet connection, and will take about an hour or so.
 7. Now, create autoscripts on the target. These are all in the form `scripts/auto_$X.sh`, creating as many as you'd like (they have to start with start with `auto_`). You can copy `auto_nothing.sh` to get started.
 8. After some tweaking, run `sudo ./scripts/update_raspi.sh` which should update the `/etc/rc.local` file to include all autoscripts. You will need to run `sudo ./scripts/update_raspi.sh` each time you add or remove an autoscript.

You should have it!

Now, you should still be able to connnect via `raspberrypi.local`, or `10.TE.AM.RPI`.

