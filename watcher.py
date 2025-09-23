from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class Watcher(FileSystemEventHandler):
    def __init__(self, procesar_archivo_func):
        self.procesar_archivo_func = procesar_archivo_func

    def on_created(self, event):
        if not event.is_directory:
            print(f"Nuevo archivo detectado: {event.src_path}")
            self.procesar_archivo_func(event.src_path)

def start_watch(folder_path, procesar_archivo_func):
    event_handler = Watcher(procesar_archivo_func)
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=True)  # <- aquí es recursivo
    observer.start()
    print(f"Monitoreando carpeta: {folder_path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
