# RobotExtra

This is the Py-cord branch.

The old Discord.py version can be found [here](https://github.com/ExtraRandom/RobotExtra/tree/discord.py) but it is no longer maintained.


The bot is now able to run on docker.
Below are some commands used for doing so.


[Build instructions](docs/docker_build.md)

### Run docker image

````shell
docker run -d \
    --name robot_extra \
    --restart=unless-stopped \
    -v /path_to_docker_volumes_folder/discord/logs:/app/logs \
    -v /path_to_docker_volumes_folder/discord/configs:/app/configs \
    extrarandom/robot_extra:master
````


### Updating
Remove the old image
````shell
docker stop robot_extra
docker rm robot_extra
````
Then run the docker image using the above command


# Example
```shell
docker run -d \
    --name robot_extra \
    --restart=unless-stopped \
    -v /home/thomas/Desktop/docker/discord/logs:/app/logs \
    -v /home/thomas/Desktop/docker/discord/configs:/app/configs \
    extrarandom/robot_extra:master
```