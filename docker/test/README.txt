#####################
# Docker TEST Setup #
#####################

This directory contains the files to run a test instance of OpenL2M in a docker container, using "docker compose"

Note: this is NOT meant to become a production setup!!!

Below are steps that appear to work, with some additional testing hints...

Requirements:
    - a working docker host.
    - rights to create new containers.
    - working knowledge of using docker with compose.

Test Setup Steps:
-----------------

1 - Clone the repo, into /opt/openl2m
    cd /opt
    git clone https://github.com/openl2m/openl2m

2 - Cd into the docker/test working directory
    cd openl2m/docker/test

Note: the following steps assume installation in the default directory, /opt/openl2m/.
If not, you will need to modify several of the docker files...

3 - Run docker:
    sudo docker compose up

If you get something like this, things are running:
    openl2m-1   |   Applying ...
    openl2m-1   | Updating Wireshark Ethernet database...
    openl2m-1   | Initialization done!

Test from a browser, to "http://<your-host>:8000/". If you get the login screen, things are running!
Now hit Control-C, and run as a daemon:

    sudo docker compose up -d

4 - Open a shell to the "openl2m" container, to create the superuser account:

    sudo docker exec -ti test-openl2m-1 bash

    In this new shell, run:
    python3 manage.py createsuperuser

    and then:
    exit
    to get back to the host environment.

5 - go back to the web site, login and test as needed!

NOTE: this does NOT include the documentation on the web site...

6 - stop when done. Run:

    sudo docker compose down


Other Things:
------------
* To clean up and rebuild the OpenL2M container to test new code (and leave the database intact):

    git pull
    sudo docker compose build openl2m

Be patient, this copies files again, and reinstalls the python dependencies...
Next run this to restart the containers:

    sudo docker compose up -d


* To clean up most *everything*, run:

    sudo docker compose down
    sudo docker image rm openl2m:localbuild
    sudo docker volume rm test_postgres_data


