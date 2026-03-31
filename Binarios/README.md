## Visualizers

- If you wanna have this project on a **Desktop/Mobile** app you have this littles programs to view the web like an APP
### Desktop visualizer:
- For **Win** / **Linux**  you have `/ViusalizadorEscritorio` that contains a *Python* file using `PYQT6` that answer to put the IP/HOST and port to connect and after that it deploy the web on a Desktop app
- To run it install the dependencies and run this on the `/ViusalizadorEscritorio` root:
	- PyQt6
	- PyQt6-WebEngine

```bash
pip install PyQt6
pip install PyQt6-WebEngine
python visualizer.py
```

- Or if you wanna compile it on Windows, run this:

```bash
pip install pyinstaller
pyinstaller --name MusicCloudServer --onedir visualizer.py
```

### Android Visualizer:
> In releases will be the original **APK** 

If you wanna compile it by your self you will need [Android Studio](https://developer.android.com/studio)

- If you wanna compile it by your self open the `/VisualizadorAndroid` root with the *Android Studio* as a Proyect
- Wait till graddle syncronize
- Go to Build → Generate Signed Bundle/APK → APK
#### How to use the visualizer?
1. The first time running the app will show a dialogue with inputs:
   - **Protocol**: `http` o `https`
   - **IP / Host**: p.ej. `192.168.1.100` o `miservidor.local`
   - **Port** (optional): p.ej. `8080`
1. Touch "Conectar" → to load the web
2. To change the web selected: go to menu (3 points menu) → Configurar servidor
