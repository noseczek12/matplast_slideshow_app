# app.py

import os
import time
from threading import Lock
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

# --- Konfiguracja ---
SLIDESHOW_INTERVAL = 5  # Czas w sekundach
IMAGE_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# --- Inicjalizacja Aplikacji ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = IMAGE_FOLDER
app.config['SECRET_KEY'] = 'twoj-bardzo-tajny-klucz-do-flash-messages!'
socketio = SocketIO(app, async_mode='eventlet')

# Zmienne globalne i blokada wątku
thread = None
thread_lock = Lock()
photos = []
current_photo_index = 0

# --- Funkcje pomocnicze ---
def allowed_file(filename):
    """Sprawdza, czy plik ma dozwolone rozszerzenie."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def refresh_photos():
    """Wątkowo-bezpieczna funkcja do odświeżania globalnej listy zdjęć."""
    global photos, current_photo_index
    with thread_lock:
        valid_extensions = ('.png', '.jpg', 'jpeg', '.gif', '.webp')
        photo_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(valid_extensions)]
        photos = sorted(photo_files)
        # Resetuj indeks, aby uniknąć błędu, gdy usuniemy aktualne zdjęcie
        current_photo_index = 0
        print(f"Odświeżono listę. Znaleziono {len(photos)} zdjęć.")

# --- Logika pokazu slajdów w tle ---
def background_slideshow_thread():
    """Wątek działający w tle, który cyklicznie zmienia zdjęcia."""
    global current_photo_index
    while True:
        socketio.sleep(SLIDESHOW_INTERVAL)
        with thread_lock:
            if not photos:
                continue # Pomiń, jeśli nie ma zdjęć
            
            current_photo_index = (current_photo_index + 1) % len(photos)
            photo_url = f'/{IMAGE_FOLDER}/{photos[current_photo_index]}'
            
        # Wyślij aktualizację do wszystkich kiosków
        socketio.emit('update_image', {'url': photo_url})
        print(f"Kiosk: Zmieniono zdjęcie na: {photos[current_photo_index]}")

# --- Trasy (Routes) aplikacji webowej ---
@app.route('/')
def kiosk():
    """Główny widok publicznego kiosku."""
    return render_template('kiosk.html')

@app.route('/admin')
def admin_panel():
    """Panel administratora pokazujący obecne zdjęcia i formularze."""
    return render_template('admin.html', photos=photos)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Obsługa wgrywania nowego zdjęcia."""
    if 'file' not in request.files:
        flash('Nie wybrano pliku')
        return redirect(url_for('admin_panel'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Nie wybrano pliku')
        return redirect(url_for('admin_panel'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        refresh_photos() # Odśwież listę zdjęć po dodaniu nowego
        flash(f'Zdjęcie "{filename}" zostało dodane.')
    else:
        flash('Niedozwolony format pliku.')
        
    return redirect(url_for('admin_panel'))

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    """Obsługa usuwania zdjęcia."""
    try:
        # Zabezpieczenie: upewnij się, że nazwa pliku jest bezpieczna
        safe_filename = secure_filename(filename)
        if safe_filename != filename:
            raise ValueError("Niedozwolona nazwa pliku.")

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            refresh_photos() # Odśwież listę po usunięciu
            flash(f'Zdjęcie "{safe_filename}" zostało usunięte.')
        else:
            flash('Nie znaleziono takiego pliku.')
    except Exception as e:
        flash(f'Wystąpił błąd podczas usuwania: {e}')
        
    return redirect(url_for('admin_panel'))

# --- Logika Socket.IO ---
@socketio.on('connect')
def handle_connect():
    """Obsługa połączenia nowego klienta (kiosku)."""
    global thread
    print('Nowy klient kiosku połączony!')
    
    with thread_lock:
        if thread is None:
            refresh_photos() # Wczytaj zdjęcia przy pierwszym uruchomieniu
            thread = socketio.start_background_task(target=background_slideshow_thread)

    # Wyślij nowemu klientowi aktualne zdjęcie, żeby nie zaczynał od pustego ekranu
    with thread_lock:
        if photos:
            photo_url = f'/{IMAGE_FOLDER}/{photos[current_photo_index]}'
            emit('update_image', {'url': photo_url})

# --- Uruchomienie serwera ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)