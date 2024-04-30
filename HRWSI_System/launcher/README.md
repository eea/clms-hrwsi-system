# Launcher

This directory contains the code of the Launcher.

The goal of the Launcher is to create Nomad job dispatch and Processing status workflow for Processing tasks ready to launch. A Processing tasks is ready to launch if it's preceding task is processed or null and associate Nomad job doesn't already exist.

We can find the UML of the Launcher [here](https://drive.google.com/file/d/1L7hkiG8v1X19En8pyqqQIVEiEDle2uw4/view?usp=sharing).

## Directory structure

- The *[Launcher](launcher.py)* create and associate Nomad job to Processing tasks ready to launch.
