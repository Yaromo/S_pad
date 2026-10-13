import sys
from files import *
from mixer import SinkMixer
from pw import *
import soundcard as sc
from hotkeys import HotkeyWorker
from ui import S_pad, on_app_exit, config
from PyQt6.QtWidgets import QApplication



if __name__ == "__main__":
    try:
        mixer = SinkMixer()
        pw_proc, pw_proc2, sink_name, sink_name2 = create_pipewire_cable()
        for s in sc.all_speakers():
            if s.name == 'Music_Sender':
                device = s
                break
        
        if config['micro'] != "None":
            mic_name = get_microphone_name(config['micro']) # Выбор микрофона
        try:
            connect_to_cable(mic_name)
            connect_to_cable('m_sender', get_microphone_name(config["audio"], False), False, False)
        except:
            exit()
            
        mixer.start(device) 
    except:
        pw_proc.terminate()
        pw_proc2.terminate()
        exit()
    try:
        h_worker = HotkeyWorker()
        h_worker.start_listening()
        app = QApplication(sys.argv)
        window = S_pad(mixer, h_worker, config)
        app.aboutToQuit.connect(lambda: on_app_exit(mixer, pw_proc, pw_proc2, h_worker))
        window.show()
        sys.exit(app.exec())
    except : # на всякий случай
        pw_proc.terminate()
        pw_proc2.terminate()
        mixer.stop()
        h_worker.stop_listening()