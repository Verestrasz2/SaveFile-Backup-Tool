import requests
import os
import time
import psutil
import subprocess

# --- KONFIGURATION ---
GITHUB_VERSION_URL = 'https://raw.githubusercontent.com/Verestrasz2/SaveFile-Backup-Tool/master/version.txt'
GITHUB_EXE_URL = 'https://github.com/Verestrasz2/SaveFile-Backup-Tool/releases/download/GameFile/save-backup.exe'
LOCAL_EXE = 'save-backup.exe'
LOCAL_VERSION_FILE = 'version.txt'

def kill_process(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
            print(f"Beende Prozess: {proc.info['name']} (PID {proc.info['pid']})")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                proc.kill()

def download_new_exe():
    try:
        response = requests.get(GITHUB_EXE_URL, stream=True)
        response.raise_for_status()
        with open(LOCAL_EXE, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Neue Version erfolgreich heruntergeladen.")
        return True
    except Exception as e:
        print(f"Fehler beim Herunterladen: {e}")
        return False

def update_version_file():
    try:
        response = requests.get(GITHUB_VERSION_URL)
        response.raise_for_status()
        with open(LOCAL_VERSION_FILE, 'w') as f:
            f.write(response.text.strip())
        print("version.txt erfolgreich aktualisiert.")
    except Exception as e:
        print(f"Fehler beim Aktualisieren der version.txt: {e}")

def main():
    print("Updater gestartet...")

    # Schritt 1: Beende die alte App
    kill_process(LOCAL_EXE)

    # Kurze Pause, um sicherzugehen, dass Prozess beendet ist
    time.sleep(1)

    # Schritt 2: Lade neue EXE herunter
    if download_new_exe():
        # Schritt 3: version.txt aktualisieren
        update_version_file()

        # Schritt 4: neue App starten
        print("Starte neue Version...")
        subprocess.Popen([LOCAL_EXE])
    else:
        print("Update fehlgeschlagen.")

if __name__ == "__main__":
    main()
