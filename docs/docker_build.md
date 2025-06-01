## All of these may need to be ran with sudo

Log in
```shell
sudo docker login
```

Setting up a new builder
```shell
# check existing builders
docker buildx ls

# create a new builder called multi and set it as default for buildx
docker buildx create \
  --name=multi --bootstrap --platform linux/amd64,linux/arm64 --use

```

Build
```shell
sudo docker buildx build \
  -t extrarandom/robot_extra:master \
  --progress plain \
  --platform linux/amd64,linux/arm64 \
  --push \
  .
```