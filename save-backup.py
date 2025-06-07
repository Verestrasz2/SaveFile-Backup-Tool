import os
import json
import shutil
import datetime
import subprocess
import requests
from PyQt5 import sip
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QFileDialog, QComboBox,
    QLabel, QListWidgetItem, QInputDialog, QMessageBox,
    QMenu
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, QPoint
from PyQt5.QtWidgets import (
    QGroupBox, QSizePolicy, QScrollArea, QAbstractItemView
)

__version__ = "1.0.0"  # aktuelle Script-Version

SAVE_FILE = "save_paths.json"
BACKUP_DIR = "Backups"
ICON_DIR = "icons"

class BackupApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Savegame Backup Tool")
        self.setWindowIcon(QIcon("icons/saveicon.png"))
        self.setGeometry(100, 100, 800, 400)

        self.savegames = self.load_savegames()
        self.selected_game = None

        self.setup_ui()
        self.save_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.save_list.customContextMenuRequested.connect(self.savefile_context_menu)

        # Versionscheck beim Start
        self.check_for_update()

    def check_for_update(self):
        """
        Vergleicht lokale version.txt (optional) und Online-Version auf GitHub.
        Wenn Update verfügbar: fragt Benutzer.
        Startet updater.exe bei Zustimmung und beendet Programm.
        """
        local_version = __version__

        # Versuch, lokale version.txt zu lesen, falls vorhanden
        local_version_file = "version.txt"
        if os.path.exists(local_version_file):
            try:
                with open(local_version_file, "r", encoding="utf-8") as f:
                    local_version = f.read().strip()
            except Exception:
                pass  # fallback auf __version__

        # Online-Version von GitHub holen
        github_version_url = 'https://raw.githubusercontent.com/Verestrasz2/SaveFile-Backup-Tool/master/version.txt'
        try:
            resp = requests.get(github_version_url, timeout=5)
            if resp.status_code == 200:
                online_version = resp.text.strip()
                if self.is_newer_version(online_version, local_version):
                    # Frage zum Update
                    res = QMessageBox.question(
                        self,
                        "Update verfügbar",
                        f"Eine neue Version {online_version} ist verfügbar.\n"
                        f"Du hast Version {local_version}.\n"
                        "Möchtest du jetzt updaten?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if res == QMessageBox.Yes:
                        self.run_updater()
        except Exception:
            # Online-Version nicht erreichbar - ignoriere
            pass

    def is_newer_version(self, online, local):
        """Vergleicht Versionsstrings, Return True wenn online > local"""
        def to_tuple(v):
            return tuple(int(x) for x in v.split(".") if x.isdigit())
        try:
            return to_tuple(online) > to_tuple(local)
        except Exception:
            return False

    def run_updater(self):
        """
        Startet updater.exe und beendet das Hauptprogramm.
        """
        updater_path = "updater.exe"  # Pfad zur updater.exe, ggf. anpassen
        try:
            subprocess.Popen([updater_path])
        except Exception as e:
            QMessageBox.warning(self, "Update-Fehler", f"Updater konnte nicht gestartet werden:\n{e}")
            return
        QApplication.quit()

    def setup_ui(self):
        self.setMinimumSize(900, 500)
        self.resize(1100, 600)

        # Dark Theme
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3c3f41;
                border: 1px solid #555;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #4e5254;
            }
            QComboBox, QListWidget {
                background-color: #3c3f41;
                border: 1px solid #555;
            }
            QGroupBox {
                border: 1px solid #666;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
        """)

        main_layout = QVBoxLayout()

        # Obere Leiste mit Spielauswahl und Buttons
        top_layout = QHBoxLayout()
        self.game_dropdown = QComboBox()
        self.game_dropdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.game_dropdown.currentIndexChanged.connect(self.change_game)

        self.add_game_btn = QPushButton("+ Add Game")
        self.edit_game_btn = QPushButton("Edit Game")
        self.help_btn = QPushButton("Anleitung")
        self.help_btn.clicked.connect(self.show_help_dialog)
        top_layout.addWidget(self.help_btn)

        self.add_game_btn.clicked.connect(self.add_game)
        self.edit_game_btn.clicked.connect(self.show_game_edit_menu)

        top_layout.addWidget(QLabel("Game:"))
        top_layout.addWidget(self.game_dropdown)
        top_layout.addWidget(self.add_game_btn)
        top_layout.addWidget(self.edit_game_btn)
        main_layout.addLayout(top_layout)

        # Hauptbereich
        list_layout = QHBoxLayout()

        # --- Savegame-List (Left)
        save_group = QGroupBox("Savegame Files")
        save_layout = QVBoxLayout()

        self.save_list = QListWidget()
        self.save_list.setIconSize(QSize(32, 32))
        self.save_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.save_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        save_layout.addWidget(self.save_list)

        save_group.setLayout(save_layout)
        list_layout.addWidget(save_group, 4)

        # --- Middle Buttons
        button_layout = QVBoxLayout()
        self.backup_btn = QPushButton("→ Backup")
        self.restore_btn = QPushButton("← Restore")
        self.backup_btn.clicked.connect(self.backup_savegame)
        self.restore_btn.clicked.connect(self.restore_savegame)

        button_layout.addStretch()
        button_layout.addWidget(self.backup_btn)
        button_layout.addWidget(self.restore_btn)
        button_layout.addStretch()

        list_layout.addLayout(button_layout, 1)

        # --- Backup-List (Right)
        backup_group = QGroupBox("Backups")
        backup_layout = QVBoxLayout()

        self.backup_list = QListWidget()
        self.backup_list.setIconSize(QSize(32, 32))
        self.backup_list.setSelectionMode(QListWidget.SingleSelection)
        self.backup_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.backup_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.backup_list.customContextMenuRequested.connect(self.backup_context_menu)
        self.backup_list.itemDoubleClicked.connect(self.edit_note)

        backup_layout.addWidget(self.backup_list)
        backup_group.setLayout(backup_layout)
        list_layout.addWidget(backup_group, 4)

        main_layout.addLayout(list_layout)
        self.setLayout(main_layout)

        self.refresh_game_dropdown()

    def add_game(self):
        path = QFileDialog.getExistingDirectory(self, "Savegame-Verzeichnis wählen")
        if path:
            name, ok = QInputDialog.getText(self, "Spielname", "Name des Spiels:")
            if ok and name:
                icon_path, _ = QFileDialog.getOpenFileName(self, "Icon auswählen", "", "Bilder (*.png *.jpg *.ico)")
                if icon_path:
                    os.makedirs(ICON_DIR, exist_ok=True)
                    icon_dest = os.path.join(ICON_DIR, f"{name}.png")
                    shutil.copy(icon_path, icon_dest)
                else:
                    icon_dest = ""

                self.savegames[name] = {"path": path, "icon": icon_dest}
                self.save_savegames()
                self.refresh_game_dropdown()
                self.game_dropdown.setCurrentText(name)

    def show_help_dialog(self):
        help_text = (
            "<b>Willkommen beim Savegame Backup Tool!</b><br><br>"
            "<b>Allgemeine Funktionen:</b><br>"
            "• Links: Savegame-Dateien und Ordner aus dem Spielordner<br>"
            "• Rechts: Backups dieser Dateien, sortiert nach Datum<br>"
            "• Mittig: Mit den Pfeil-Buttons kannst du Backups erstellen oder wiederherstellen<br><br>"

            "<b>Rechtsklick-Funktionen:</b><br>"
            "• <u>Links (Savegame-Dateien):</u> Löschen oder Umbenennen von Savegame-Dateien<br>"
            "• <u>Rechts (Backup-Einträge):</u> Löschen oder Umbenennen von Backup-Ordnern<br><br>"

            "<b>Doppelklick:</b><br>"
            "• <u>Backup-Eintrag (rechts):</u> Notiz zum Backup anzeigen/bearbeiten<br><br>"

            "<b>Tipp:</b><br>"
            "• Du kannst mehrere Dateien gleichzeitig auswählen, indem du Strg gedrückt hältst.<br>"
            "• Spiel-Icons können automatisch geladen oder manuell gesetzt werden.<br>"
            "• Das Layout passt sich der Fenstergröße an.<br>"
        )

        QMessageBox.information(self, "Anleitung", help_text)

    def show_game_edit_menu(self):
        if not self.selected_game:
            QMessageBox.warning(self, "Kein Spiel ausgewählt", "Bitte zuerst ein Spiel auswählen.")
            return

        menu = QMenu()

        action_icon = menu.addAction("🖼 Icon ändern")
        action_path = menu.addAction("📁 Pfad ändern")
        action_delete = menu.addAction("🗑 Spiel löschen")

        action = menu.exec_(self.edit_game_btn.mapToGlobal(self.edit_game_btn.rect().bottomLeft()))
        game = self.selected_game

        if action == action_icon:
            icon_path, _ = QFileDialog.getOpenFileName(self, "Neues Icon", "", "Bilder (*.png *.jpg *.ico)")
            if icon_path:
                dest = os.path.join(ICON_DIR, f"{game}.png")
                shutil.copy(icon_path, dest)
                self.savegames[game]["icon"] = dest
                self.save_savegames()
                self.refresh_lists()

        elif action == action_path:
            new_path = QFileDialog.getExistingDirectory(self, "Neuer Savegame-Pfad")
            if new_path:
                self.savegames[game]["path"] = new_path
                self.save_savegames()
                self.refresh_lists()

        elif action == action_delete:
            confirm = QMessageBox.question(self, "Löschen bestätigen", f"{game} wirklich löschen?", QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                self.savegames.pop(game)
                self.save_savegames()
                self.refresh_game_dropdown()
                self.save_list.clear()
                self.backup_list.clear()
                self.selected_game = None

    def change_game(self, index):
        if index == -1:
            return
        game = self.game_dropdown.currentText()
        self.selected_game = game
        self.refresh_lists()

    def refresh_game_dropdown(self):
        self.game_dropdown.clear()
        self.game_dropdown.addItems(self.savegames.keys())

    def refresh_lists(self):
        self.save_list.clear()
        self.backup_list.clear()
        if not self.selected_game:
            return

        data = self.savegames[self.selected_game]
        path = data["path"]
        icon_path = data.get("icon", "")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        # Savegames anzeigen (Dateien/Ordner im Savegame-Ordner)
        if os.path.exists(path):
            for fname in os.listdir(path):
                item = QListWidgetItem(fname)
                item.setIcon(icon)
                self.save_list.addItem(item)

        # Backups sortiert anzeigen
        b_path = os.path.join(BACKUP_DIR, self.selected_game)
        if os.path.exists(b_path):
            backups = os.listdir(b_path)

            def parse_date(name):
                try:
                    return datetime.datetime.strptime(name, "%d.%m.%Y_%H-%M-%S")
                except ValueError:
                    return datetime.datetime.min

            backups.sort(key=parse_date, reverse=True)  # Neueste zuerst

            notes = self.savegames[self.selected_game].get("notes", {})

            for date in backups:
                item = QListWidgetItem(date)
                item.setIcon(icon)
                if note := notes.get(date):
                    item.setToolTip(note)
                self.backup_list.addItem(item)

    def backup_savegame(self):
        if not self.selected_game:
            return

        selected_files = self.save_list.selectedItems()
        if not selected_files:
            QMessageBox.warning(self, "Keine Dateien ausgewählt", "Bitte wähle mindestens eine Datei links aus.")
            return

        src_path = self.savegames[self.selected_game]["path"]
        if not os.path.exists(src_path):
            QMessageBox.warning(self, "Pfad nicht gefunden", "Savegame-Pfad existiert nicht.")
            return

        now = datetime.datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        dst = os.path.join(BACKUP_DIR, self.selected_game, now)
        os.makedirs(dst, exist_ok=True)

        copied_files = []

        for item in selected_files:
            filename = item.text()
            src_file = os.path.join(src_path, filename)
            dst_file = os.path.join(dst, filename)

            try:
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)
                elif os.path.isdir(src_file):
                    shutil.copytree(src_file, dst_file)
                copied_files.append(filename)  # Datei wurde kopiert
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Fehler beim Kopieren von {filename}: {e}")

        # Speichere die Liste der Dateien als Notiz zum Backup
        notes = self.savegames[self.selected_game].setdefault("notes", {})
        notes[now] = "Backed up files:\n" + "\n".join(copied_files)
        self.save_savegames()

        QMessageBox.information(self, "Backup erstellt", f"Backup mit {len(copied_files)} Datei(en) wurde erstellt.")
        self.refresh_lists()

    def restore_savegame(self):
        if not self.selected_game:
            return

        selected_backup = self.backup_list.currentItem()
        if not selected_backup:
            QMessageBox.warning(self, "Kein Backup ausgewählt", "Bitte wähle ein Backup aus der rechten Liste.")
            return

        backup_date = selected_backup.text()
        backup_path = os.path.join(BACKUP_DIR, self.selected_game, backup_date)
        savegame_path = self.savegames[self.selected_game]["path"]

        if not os.path.exists(backup_path):
            QMessageBox.warning(self, "Backup nicht gefunden", "Backup-Ordner existiert nicht.")
            return

        # Statt komplettes Verzeichnis zu löschen, Dateien einzeln kopieren / überschreiben
        try:
            for root, dirs, files in os.walk(backup_path):
                # Zielverzeichnis entsprechend der Struktur ermitteln
                relative_path = os.path.relpath(root, backup_path)
                target_dir = os.path.join(savegame_path, relative_path)
                os.makedirs(target_dir, exist_ok=True)

                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(target_dir, file)
                    shutil.copy2(src_file, dst_file)  # überschreibt automatisch, falls Datei existiert

        except Exception as e:
            QMessageBox.warning(self, "Fehler", f"Fehler beim Wiederherstellen: {e}")
            return

        QMessageBox.information(self, "Wiederhergestellt", f"Backup {backup_date} wurde wiederhergestellt.")
        self.refresh_lists()

    def savefile_context_menu(self, pos: QPoint):
        item = self.save_list.itemAt(pos)
        if not item or not self.selected_game:
            return

        filename = item.text()
        game_path = self.savegames[self.selected_game]["path"]
        full_path = os.path.join(game_path, filename)

        menu = QMenu()
        delete_action = menu.addAction("🗑 Datei/Ordner löschen")
        rename_action = menu.addAction("✏️ Umbenennen")

        action = menu.exec_(self.save_list.viewport().mapToGlobal(pos))

        if action == delete_action:
            confirm = QMessageBox.question(self, "Löschen bestätigen", f"Soll '{filename}' wirklich gelöscht werden?",
                                           QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                try:
                    if os.path.isfile(full_path):
                        os.remove(full_path)
                    elif os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    self.refresh_lists()
                except Exception as e:
                    QMessageBox.warning(self, "Fehler", f"Fehler beim Löschen: {e}")

        elif action == rename_action:
            new_name, ok = QInputDialog.getText(self, "Umbenennen", "Neuer Name:", text=filename)
            if ok and new_name and new_name != filename:
                new_path = os.path.join(game_path, new_name)
                if os.path.exists(new_path):
                    QMessageBox.warning(self, "Fehler", "Eine Datei/Ordner mit diesem Namen existiert bereits.")
                    return
                try:
                    os.rename(full_path, new_path)
                    self.refresh_lists()
                except Exception as e:
                    QMessageBox.warning(self, "Fehler", f"Umbenennen fehlgeschlagen: {e}")

    def edit_note(self, item):
        if not self.selected_game:
            return

        text, ok = QInputDialog.getMultiLineText(self, "Notiz bearbeiten", f"Notiz zu Backup {item.text()}:", item.toolTip())
        if ok:
            notes = self.savegames[self.selected_game].setdefault("notes", {})
            notes[item.text()] = text
            self.save_savegames()
            item.setToolTip(text)

    def backup_context_menu(self, pos: QPoint):
        item = self.backup_list.itemAt(pos)
        if not item:
            return

        menu = QMenu()
        delete_action = menu.addAction("Backup löschen")
        rename_action = menu.addAction("Backup umbenennen")

        action = menu.exec_(self.backup_list.viewport().mapToGlobal(pos))
        if action == delete_action:
            reply = QMessageBox.question(self, "Backup löschen", f"Backup '{item.text()}' wirklich löschen?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                backup_path = os.path.join(BACKUP_DIR, self.selected_game, item.text())
                try:
                    if os.path.exists(backup_path):
                        shutil.rmtree(backup_path)
                    # Backup auch aus Notizen entfernen, falls vorhanden
                    notes = self.savegames[self.selected_game].get("notes", {})
                    if item.text() in notes:
                        del notes[item.text()]
                        self.save_savegames()
                    self.refresh_lists()
                except Exception as e:
                    QMessageBox.warning(self, "Fehler", f"Löschen fehlgeschlagen: {e}")

        elif action == rename_action:
            old_name = item.text()
            new_name, ok = QInputDialog.getText(self, "Backup umbenennen", "Neuer Name für das Backup:", text=old_name)
            if ok and new_name and new_name != old_name:
                old_path = os.path.join(BACKUP_DIR, self.selected_game, old_name)
                new_path = os.path.join(BACKUP_DIR, self.selected_game, new_name)

                if os.path.exists(new_path):
                    QMessageBox.warning(self, "Fehler", "Ein Backup mit diesem Namen existiert bereits.")
                    return

                try:
                    os.rename(old_path, new_path)
                    # Notizen umbenennen
                    notes = self.savegames[self.selected_game].get("notes", {})
                    if old_name in notes:
                        notes[new_name] = notes.pop(old_name)
                        self.save_savegames()
                    self.refresh_lists()
                except Exception as e:
                    QMessageBox.warning(self, "Fehler", f"Umbenennen fehlgeschlagen: {e}")

    def save_savegames(self):
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.savegames, f, indent=2, ensure_ascii=False)

    def load_savegames(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

if __name__ == "__main__":
    app = QApplication([])
    window = BackupApp()
    window.show()
    app.exec_()
