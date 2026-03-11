# MusicCloudServer_TFG

>`Project version: 2.3.2`  (This value will be updated on every funcionality change in the project)

> ***About this version: In the last version, Fixed bugs, reduced the number of lines in the JS and added funcionality to change the password in admin panel . Features/Bugs to add/fix: need to fix ban field (inline field) and update rol (inline field) need to add funcionality to remove playlists***


> This project is under license. Please check the LICENSE file for legal information. Feel free to use the program, but be aware of the license policy, as any type of commercial use is explicitly prohibited. It is delivered without warranty, and any changes, modifications, or integrations will be the property of the original author. The author of this project is not responsible for any problems the software may cause, and any changes or modifications to the project must include the original author's name and do not necessarily require notification.

**MusicCloudServer is the project that allow you to make your own private server to play the music you want with complete freedom. No ads, connected with youtube and you can upload your own audio files (download from youtube too!)**

## Information about the project:

- The objective of this project is to get freedom enjoying your music. This is a final degree project not finished yet, where you can currently listen to music you've downloaded and uploaded with complete freedom.

- This project is raised to connect whenever and anywhere. First of all the firewall in your local machine where running the project will need to be able for listen in the port 8080 (Web Server port used), then you can expose your local network to connect from the exterior or used a private VPN to connect from the IP it gave you. I reccomend the last one if you more privacy.

    - VPN recommended: https://www.zerotier.com (Free 3 Networks and 10 Devices)

- Future implementations that will be made:
    - ~~user role management (database protection)~~
    - user stats (Database)
    - ~~server stats (System usage) (Operative Systems) - Will be used to check minimum requirements to run the project~~
    - ~~local playlists (Database)~~
    - desktop application (App)
    - mobile application (App)
    - route to play audio/videos from youtube (Web/App)
    - funcionality that allow to download audio from youtube automatically 
    - importing youtube playlists

## Use and desplegation of the project:

***This project is multiplatform:***

- In Windows you will need Docker to run it (For easier deployment):
    - You will find in the root path a file called `BuildDocker.bat`, it will drop down the containers if they already exists and build it. The Dockerfile is responsible for installing dependencies, exposing ports etc. The docker-compose.yml create the containers, networks etc.

    - Run the `BuildDocker.bat` or run this in a **CMD**:

    ```bash
    docker compose down -v
    docker compose build --no-cache
    docker compose up
    ```

    - It will create the containers: 1 for the web service and another for the DataBase (`MySQL`)

- In Linux you will need to setup your own MySQL server, when you setup the server configure the variables in .env with your user and password. You will need to change the music folder with the path you will put the local music files too

### To use the project:

- This project actually is only web service (You can use in the machine it local running searching localhost:8080 or in your local network searching <vm_ip>:8080). In subsequent versions i will add a Desktop and mobile Application to connect to the server for a better use (A machine will need to host the server to centralize the use of resources). 

- The project automatically manage the Database creating a first admin user (It is created in the script.sql file in `/src/resources` which is automatically loaded every first run of the project). The user is `'koan'`, password `'koan'` that this user can access to the admin panel and create more users and manage them, so that everything related to the database can be managed from within the project itself without you having to write any more code manually.