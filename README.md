# Reflector Lite
### A small Reflector for LBRY data network. Caches blobs only for selected channels and does this eagerly.

The LBRY data network splits the data you upload in some small blobs and distributes them among several peers. 
When somebody wants to watch/download some content, that device will query this peer network and start retrieving those 
blobs. If there are not enoug peers around or they are slow, the "user experience" quality drops.

There are easier ways to help with this availability issue, but with far less control: 
 - Desktop app: [https://lbry.com/get](https://lbry.com/get)
 - Install and run lbry-api

This app lets you automatically download content from selected channels and with this, the content's blobs will always
be available.

## Use cases

 - **You want to cache/seed your own videos**. Maybe you are afraid that older videos will not be properly reflected by 
   the network, or you want them to be always available in some geographical region. All these, without leaving the Desktop
   app running or worrying if the desktop app picked your video blobs.
 
- You want to **support your favourite channels** and want to be able to watch their videos without hiccups. You can 
   deploy this reflector nearby (network wise), and your devices will probably pick it up as a blob source peer.

- You don't want to deploy a full blown reflector.

- You want the lbry contained and without worrying about configurations and data handling
 

## Quick and dirty setup:

Requirements: 
 - A linux machine
 - docker installed
 - docker-compose installed

1) Download the git archive (either clone the repo or download the zip)

2) Unpack into a folder and go there.

3) Configure the channel list (see channel_list_sample.txt file) 

4) Run ``bash ./start.sh``

## Longer presentation

### Overview

This code should run on a "always on" Linux machine. There are two components, the ``lbry-sdk`` at v0.97.0 and a python script that
queries and downloads content.

Each component runs in its own docker and the whole app's timeline is handled by docker-compose.

There are two ports exposed publicly, 3333 and 4444. The port 5279 is exposed only to localhost. Make sure that 3333 and 4444 are routable.
Use [https://canyouseeme.org](https://canyouseeme.org) to check.

### Lbry sdk specific options

The data lbry-sdk generates can be stored locally. Create a file called ``config.txt`` that contains ``LBRY_API_DATA_FOLDER=/some/folder``.
Check the ``config_sample.txt`` file for an example. You would want to have the data folder pointing to some large partition.

This also enables a faster startup for the app, because all the data is there. Otherwise, the data will be saved in the docker
container and of course, it must be re-downloaded each time the app restarts.

### List channels to cache

Each channel that you want to mirror/cache must be specified in the ``channel_list.txt`` file. Again, there is an example in
``channel_list_sample.txt``.

Each row must contain an lbry url for channel or the channel name. For now, http odysee links are not working. 
Example: Instead of ``https://odysee.com/@kauffj:f`` write ``@kauffj:f``.

Some channels can be very big (esp those mirrored from YT) so one can specify a date that will filter older videos/content.

The date is optional, but if it exists, there must be a comma and the date format must be: YYYY-MM-DD. Do not remove zero prefix.

The logic inside the python script is that this list will be scanned once evey hour and the content found at those channels
will be downloaded locally.

### Run the app

Docker and docker-compose must be installed on the machine. The simple ``start.sh`` script will configure some user IDs 
and fire up the docker-compose in detached mode. This means that once the app is running you can close the terminal and 
log off. 

    bash ./start.sh

To check if everything is working:

1) Go to the configured download folder and see if content is being added.
2) Issue ``docker-compose logs -f`` to see the outputs of the containers. At least lbry-sdk is fairly verbose. The python
   script might issue errors on startup but if the lbry-sdk is showing blob activity then everything is fine.
   The ``-f`` flag will keep listening for output but it is safe to kill with CTRL+C and it will not stop the containers.

To stop the app, run ``stop.sh``:

    bash ./stop.sh


### Python script

There is a script called ``start_api_docker.sh``. This will fire up only the lbry-api container, in interactive mode. Useful
for debugging or development.

The src/main.py script (with the parameter ``start``) reads the content of ``channel_list.txt``, parses the lines, queries
the lbry-api for channel claims and then downloads selected stream claims. Then, it waits 1h and repeats the process.

There are few options to this script, chech the python file or directly the help.

There are few requirements for the script to run system wide:
 - The lbry-api visible to some port (the url:port can be configured with -s parameter)
 - python 3.8+
 - requests python package installed.

The python script can also connect to the docker-compose started api.

## Limitations

 - uPnP does not work from docker. Ports must be manually forwarded to the local machine, if behind a NAT
 - There is no handling of disk quota. If the disk is getting full, remove some blobs and then remove some channels
 - The stream content is downloaded and decoded. Deleting these will not help.
 - No easy way of checking if the DHT network registered this node and if it is serving

## TODO

 - Watch the blockchain for new channel additions and start fetching blobs.
 - Dive deeper into lbry-api and find a way to download blobs without unpacking the whole stream. Will save disk space.
 - Check for a stream, (head blob and/or some random blobls) the peer list. Useful to see if your always-on machine 
   is seeding and is visible from another location.
 - Statistics about channels (eg how big they are)
 - Statistics about streams (number of peers, peer speed, chunk health)
 - Vanity statistics. How many chunks have been served? Are you helping or it just stays idle?
 - Filter for incoming blobs, maybe you are tight on space and don't want to host other content.


#### Useful network commands for Linux. Left here for reference
 - ``ss -ltp4``
