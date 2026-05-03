# MusicCloudServer_TFG

>`Project version: 3.5`  (This value will be updated on every funcionality change in the project)

> ***About this version: Final version with all funcionalities and visualizers for multiplatforms. Making Docs***


> This project is under license. Please check the LICENSE file for legal information. Feel free to use the program, but be aware of the license policy, as any type of commercial use is explicitly prohibited. It is delivered without warranty, and any changes, modifications, or integrations will be the property of the original author. The author of this project is not responsible for any problems the software may cause, and any changes or modifications to the project must include the original author's name and do not necessarily require notification.

**MusicCloudServer is a project that allow you to make your own private server to play the music you want with complete freedom. No ads, connected with youtube and you can upload your own audio files (download from youtube too!)**

## Project Status:

> Final version, all working.
## Information about the project:

- The objective of this project is to get freedom enjoying your music. This is a final degree project not finished yet, where you can currently listen to music you've downloaded and uploaded with complete freedom.

- This project is raised to connect whenever and anywhere. First of all the firewall in your local machine where running the project will need to be able for listen in the port 8080 (Web Server port used), then you can expose your local network to connect from the exterior or used a private VPN to connect from the IP it gave you. I reccomend the last one if you more privacy.

    - VPN recommended: https://www.zerotier.com (Free 3 Networks and 10 Devices)

## Use and desplegation of the project:

***This project is multiplatform,  it deploy with docker:***

```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```

- This will create 2 containers, The first container will be a MySQL server for the Database of the project and the second one will be the flask service that deploy on `<ip_vm>:8080` 
- MySQL server will have this 4 tables and it will have a admin user by default `koan@koan`:
	- `users`
	- `songs` 
	- `playlists`
	- `playlist_songs`

- To use the visualizers go check the `readme.md` located on `/Binarios` root

## Dependencies:

- **Docker Desktop**
- **MySQL Server**
- **Python 3.10+** 
- **FFMPEG**
- *Python dependencies:*
	- *Flask*
	- *Werkzeug*
	- *mysql-connector*
	- *dotenv*
	- *colorama*
	- *psutil*
	- *yt_dlp*
	- *requests*
	- ***Install this dependencies if you will use the visualizer.***
	- *PyQt6*
	- *PyQt6-WebEngine*
- *If you will compile the visualizer APK:*
	- ***Android Studio***

## Project Structure:

```
MusicCloudTFG/
├── Binarios/               # Visualizers roots and files
├── src/                    # Python code files
├── .gitignore
├── BuildDocker.bat         # Deployment file on Windows
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.tests
├── LICENSE
├── README.md               # Memoria y documentación
├── Memoria.docx
└── requirements.txt
```

## Dataflow:

![Dataflow](dataflow.png)

