# ROS2 PS4 Driver
ROS2 interface for a PS4 controller

## Note
Driver not complete, still pending publish of twist messages (but interface is ready). 

If anyone finds a need for this driver, feel free to open an issue and I'll finish up the driver asap.

## To run:
1. Install [docker](https://docs.docker.com/engine/install/)

2. Build:
```
$ docker build -t ps4_driver .
```

3. Run:
```
$ docker run --rm --network=host --ipc=host --priviledged ps4_driver
```

