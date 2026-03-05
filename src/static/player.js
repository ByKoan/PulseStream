document.addEventListener("DOMContentLoaded", () => {

const player = document.getElementById("player");
const audioSource = document.getElementById("audioSource");
const currentSongTitle = document.getElementById("currentSongTitle");

let currentSongIndex = 0;
let shuffle = false;
let loop = false;

// songs viene desde el HTML
// let songs = {{ songs | tojson }};

function loadSong(index) {

    if (songs.length === 0) return;

    if (index < 0) currentSongIndex = songs.length - 1;
    else if (index >= songs.length) currentSongIndex = 0;
    else currentSongIndex = index;

    audioSource.src = "/play/" + encodeURIComponent(songs[currentSongIndex]);

    player.load();
    player.play();

    currentSongTitle.textContent = songs[currentSongIndex];
    document.title = songs[currentSongIndex];

    // Media Session API (pantalla bloqueo / botones multimedia)
    if ('mediaSession' in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({
            title: songs[currentSongIndex],
            artist: "Desconocido",
            album: "MusicCloud",
            artwork: [
                { src: "https://via.placeholder.com/96", sizes: "96x96", type: "image/png" }
            ]
        });
    }

}

function playPause() {

    if (player.paused) {
        player.play();
    } else {
        player.pause();
    }

}

function handleNextClick() {

    if (songs.length === 0) return;

    if (shuffle) {

        let newIndex;

        do {
            newIndex = Math.floor(Math.random() * songs.length);
        } while (newIndex === currentSongIndex && songs.length > 1);

        currentSongIndex = newIndex;

    } else {

        currentSongIndex++;

        if (currentSongIndex >= songs.length) {
            currentSongIndex = 0;
        }

    }

    loadSong(currentSongIndex);

}

function handlePreviousClick() {

    if (songs.length === 0) return;

    if (player.currentTime > 3) {

        player.currentTime = 0;
        player.play();

    } else {

        if (shuffle) {

            let newIndex;

            do {
                newIndex = Math.floor(Math.random() * songs.length);
            } while (newIndex === currentSongIndex && songs.length > 1);

            currentSongIndex = newIndex;

        } else {

            currentSongIndex--;

            if (currentSongIndex < 0) {
                currentSongIndex = songs.length - 1;
            }

        }

        loadSong(currentSongIndex);

    }

}

function toggleShuffle() {

    shuffle = !shuffle;

    document.getElementById("shuffleStatus").textContent =
        shuffle ? "Activado" : "Desactivado";

}

function toggleLoop() {

    loop = !loop;

    player.loop = loop;

    document.getElementById("loopStatus").textContent =
        loop ? "Activado" : "Desactivado";

}

player.addEventListener("ended", () => {

    if (loop) {
        loadSong(currentSongIndex);
        return;
    }

    handleNextClick();

});


// Media Session botones multimedia (teclas teclado / móvil / coche)
if ("mediaSession" in navigator) {

    navigator.mediaSession.setActionHandler("play", () => {
        player.play();
    });

    navigator.mediaSession.setActionHandler("pause", () => {
        player.pause();
    });

    navigator.mediaSession.setActionHandler("previoustrack", () => {
        handlePreviousClick();
    });

    navigator.mediaSession.setActionHandler("nexttrack", () => {
        handleNextClick();
    });

}


// Exponer funciones al HTML
window.loadSong = loadSong;
window.playPause = playPause;
window.handleNextClick = handleNextClick;
window.handlePreviousClick = handlePreviousClick;
window.toggleShuffle = toggleShuffle;
window.toggleLoop = toggleLoop;


// Cargar primera canción automáticamente
loadSong(0);

});