from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import keyboard
import threading
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'

shortcuts = {}

def detect_shortcuts():
    typed_text = ""
    while True:
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

@app.route('/save_shortcut', methods=['POST'])
def save_shortcut():
    shortcut = request.form['shortcut']
    replacement = request.form['replacement']
    with open("shortcuts.txt", "a") as f:
        f.write(f"{shortcut}={replacement}\n")
    shortcuts[shortcut] = replacement
    flash(f"Shortcut '{shortcut}' saved successfully.", 'success')
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
        return jsonify({'error': 'No shortcuts selected.'}), 400
    try:
        with open("shortcuts.txt", "r") as f:
            lines = f.readlines()
        with open("shortcuts.txt", "w") as f:
            for line in lines:
                shortcut, _ = line.strip().split("=")
                if shortcut in shortcuts_to_delete:
                    continue
                f.write(line)
        return jsonify({'message': f"Shortcuts {', '.join(shortcuts_to_delete)} deleted successfully."}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    detection_thread = threading.Thread(target=detect_shortcuts)
    detection_thread.daemon = True
    detection_thread.start()
    app.run(debug=True)
