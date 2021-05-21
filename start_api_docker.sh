docker build -f docker/Dockerfile.lbryapi -t lbry_api .
docker stop lbry_api_container  && docker rm lbry_api_container
source config.txt
mkdir -p $LBRY_API_DATA_FOLDER
docker run -it --rm --name lbry_api_container \
  -u $(id -u):$(id -g) \
  -p 127.0.0.1:5279:5279 \
  -p 0.0.0.0:3333:3333 \
  -p 0.0.0.0:4444:4444 \
  -v $LBRY_API_DATA_FOLDER:/data/:rw \
  lbry_api

