from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import keyboard
import threading
import time

app = Flask(__name__)
app.secret_key = 'votre_clé_secrète'

shortcuts = {}
stop_detection_flag = False  # Initialisez la variable stop_detection_flag

@app.route('/stop_detection', methods=['GET'])
def stop_detection():
    global stop_detection_flag
    stop_detection_flag = True
    return redirect(url_for('index'))

@app.route('/start_detection', methods=['GET'])
def start_detection():
    global stop_detection_flag
    stop_detection_flag = False  # Réinitialisez le drapeau d'arrêt
    detection_thread = threading.Thread(target=detect_shortcuts)
    detection_thread.daemon = True
    detection_thread.start()
    return jsonify({'message': 'Détection démarrée avec succès.'}), 200
    
def detect_shortcuts():
    typed_text = ""
    while not stop_detection_flag:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            typed_text += event.name
            for shortcut, replacement in shortcuts.items():
                if typed_text.endswith(shortcut):
                    index = typed_text.rfind(shortcut)
                    typed_text = typed_text[:index] + replacement
                    for _ in range(len(shortcut)):
                        keyboard.send("backspace")
                    keyboard.write(replacement)
                    time.sleep(0.1)  # Attendre un peu pour éviter la répétition involontaire
                    typed_text = ""
    print("Détection arrêtée.")


@app.route('/save_shortcut', methods=['POST'])
def save_shortcut():
    shortcut = request.form['shortcut']
    replacement = request.form['replacement']
    with open("shortcuts.txt", "a") as f:
        f.write(f"{shortcut}={replacement}\n")
    shortcuts[shortcut] = replacement
    flash(f"Raccourci '{shortcut}' enregistré avec succès.", 'success')
    return redirect(url_for('index'))

@app.route('/')
def index():
    loaded_shortcuts = load_shortcuts()
    return render_template('index.html', loaded_shortcuts=loaded_shortcuts)

def load_shortcuts():
    shortcuts.clear()
    try:
        with open("shortcuts.txt", "r") as f:
            for line in f:
                if "=" in line:
                    shortcut, replacement = line.strip().split("=")
                    replacement = replacement.replace("|", "\n")
                    shortcuts[shortcut] = replacement
    except FileNotFoundError:
        print("Fichier 'shortcuts.txt' introuvable.")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
    return shortcuts

@app.route('/delete_shortcuts', methods=['POST'])
def delete_shortcuts():
    data = request.json
    shortcuts_to_delete = data.get('shortcuts', [])
    if not shortcuts_to_delete:
        return jsonify({'error': 'Aucun raccourci sélectionné.'}), 400
    try:
        with open("shortcuts.txt", "r") as f:
            lines = f.readlines()
        with open("shortcuts.txt", "w") as f:
            for line in lines:
                shortcut, _ = line.strip().split("=")
                if shortcut in shortcuts_to_delete:
                    continue
                f.write(line)
        return jsonify({'message': f"Raccourcis {', '.join(shortcuts_to_delete)} supprimés avec succès."}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    stop_detection_flag = False  # Initialisez la variable stop_detection_flag
    detection_thread = threading.Thread(target=detect_shortcuts)
    detection_thread.daemon = True
    detection_thread.start()
    app.run(debug=True)
