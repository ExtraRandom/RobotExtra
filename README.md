# RobotExtra

This is the Py-cord branch.

The old Discord.py version can be found [here](https://github.com/ExtraRandom/RobotExtra/tree/discord.py)



### Build docker image
````shell
docker build -f Dockerfile -t robot_extra .
````


### Run docker image
````shell
docker run \
--name robot_extra \
--restart=unless-stopped \
-v /path_to_docker_volumes_folder/discord/logs:/app/logs \
-v /path_to_docker_volumes_folder/discord/config/:/app/configs robot_extra
````