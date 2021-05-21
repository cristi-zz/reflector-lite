LBRY_API_DATA_FOLDER=/tmp/lbry_data/
source config.txt
mkdir -p $LBRY_API_DATA_FOLDER
UIDGID="$(id -u):$(id -g)" LBRY_API_DATA_FOLDER="${LBRY_API_DATA_FOLDER}" docker-compose up -d --build