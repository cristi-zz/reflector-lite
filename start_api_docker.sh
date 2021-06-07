# Starts the lbry_api docker in terminal mode. If the $LBRY_API_DATA_FOLDER variable is set inside the config.txt file,
# that folder will be mounted as the "data" folder for the lbry-api. Comment or delete the corresponding config.txt line
# if you want a clean copy of the lbry_api each time the docker starts (eg. testing)

# Set it if you need a fast start or want to have a lbry-api running on the long term

docker build -f docker/Dockerfile.lbryapi -t lbry_api .
docker stop lbry_api_container  && docker rm lbry_api_container

source config.txt
if [[ -v LBRY_API_DATA_FOLDER ]]
then
  echo "Creating $LBRY_API_DATA_FOLDER folder if it does not exist."
  mkdir -p $LBRY_API_DATA_FOLDER
  VOL_MOUNT="-v $LBRY_API_DATA_FOLDER:/data/:rw"
else
  echo "LBRY_API_DATA_FOLDER variable is not set. Data is kept only inside the docker."
  VOL_MOUNT=""
fi

docker run -it --rm --name lbry_api_container \
  -u $(id -u):$(id -g) \
  -p 127.0.0.1:5279:5279 \
  -p 0.0.0.0:3333:3333 \
  -p 0.0.0.0:4444:4444 \
   $VOL_MOUNT \
  lbry_api
