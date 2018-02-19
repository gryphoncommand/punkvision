# PunkVision

A realtime vision program for FRC teams.

## Installing Dependencies

If you are on a macbook (school-issued in our case), run `./scripts/install_schoolmac.sh`.

If you are on an Debian/Ubuntu distribution of linux, run `sudo ./scripts/install_opencv_debian.sh`

And then, run `pip3 install -r requirements.txt`


## Installing

Set `./TE.AM`'s contents to your team number seperated into the middle IP notation.

For example, if my team number was `3966`, `./TE.AM` contains `39.66`. If it were `235`, the file would contain `2.35`, etc.

Set `./R.PI` to the last octet for the raspberry PI's static IP address. This is important to remember, as you will need to connect via a static IP on the field, because mDNS will not work (which is how you connect via `raspberrypi.local`. Don't worry, when you are off of the FMS (back at a robotics lab), you will still be able to connect via `raspberrypi.local`. So, if I want to connect to the raspberry pi at `10.39.66.176`, I would set `./TE.AM` to `39.66`, and `./R.PI` to `176`.

Now, run `./scripts/deploy.sh`

ssh to the raspberry pi (`ssh pi@raspberrypi.local`), then `cd ~/`, and `tar xfv ~/Downloads/punkvision.tar.xz`.

Now, `cd punkvision`, and `./scripts/install_raspi.sh`.

Create some auto-starting files by copying `./scripts/auto_nothing` to something that starts with `auto_`. i.e. `./scripts/auto_ABC.sh`.

After this, run `./scripts/update_raspi.sh`. You will need to do this each time you change networking information, or add or remove an autoscript.

Now, reboot, and it should run the autostart scripts on boot!

## Raspi

The address should be `raspberrypi-3966-FRC.local`


## TODO

  + Use [cscore](http://robotpy.readthedocs.io/en/stable/vision/other.html) for streaming to the driver station (right now, you have to open a web browser)
  + Provide raspi images for teams to use
  + Add Makefile to install correct packages, and detect some things (probably not enough to warrant a ./configure step)


## BUGS

Please report bugs to the [issues](https://github.com/LN-STEMpunks/PunkVision/issues)

Here are a few common ones:

"**Could not find any downloads that satisfy the requirement opencv-python**" while installing dependencies.

  * To fix this, run `sudo pip3 install --upgrade pip`

