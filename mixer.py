import threading as th
import numpy as np
import soundfile as sf
from scipy import signal


class SinkMixer:
    def __init__(self, target_fs=44100):
        self.target_fs = target_fs
        self.active_sounds = []  # Список кортежей/объектов для быстрого перебора
        self.speaker = None
        self.block_size = 1024
        self.running = False
        self.lock = th.Lock()
        self.mode = False # 0 - режим миксера, 1 - режим одиночного звука
        self.clip = (-1.0, 1.0)
        self.pause = False

    def load_and_resample(self, file_path):
        data, fs = sf.read(file_path, dtype='float32')
        
        if data.ndim == 1:
            data = np.column_stack((data, data))
        
        if fs != self.target_fs:
            # Используем более быстрый метод или заранее готовим файлы
            num = int(len(data) * self.target_fs / fs)
            data = signal.resample(data, num)
            
        return np.ascontiguousarray(data, dtype='float32')

    def add_sound(self, file_path, volume=1):
        data = self.load_and_resample(file_path)
        with self.lock:
            # мб добавить эффекты звуков в его дату?
            if not self.mode:
                self.active_sounds.append({
                    'data': data, 
                    'volume': volume, 
                    'cursor': 0,
                    'length': len(data)
                })
            else:
                self.active_sounds = [{'data': data, 'volume': volume, 'cursor': 0, 'length': len(data)}]

    def _device_worker(self, speaker):
        try:
            with speaker.player(samplerate=self.target_fs, blocksize=self.block_size) as p:
                while self.running:
                    out_block = np.zeros((self.block_size, 2), dtype='float32')
                    
                    with self.lock:
                        # Быстрая фильтрация завершенных звуков
                        self.active_sounds = [s for s in self.active_sounds if s['cursor'] < s['length']]
                        # Делаем копию ссылок на текущие звуки для работы вне лока
                        current_sounds = list(self.active_sounds)
                        
                    if not self.pause:
                        for sound in current_sounds:
                            c = sound['cursor']
                            end = c + self.block_size
                            chunk = sound['data'][c:end]
                            actual_len = len(chunk)
                            
                            # Суммируем напрямую в out_block
                            out_block[:actual_len] += chunk * sound['volume']
                            sound['cursor'] = end

                    # Лимитер (soft clipping) работает лучше, чем жесткий clip
                    if self.clip:
                        np.clip(out_block, *self.clip, out=out_block)
                    p.play(out_block)
        except Exception as e:
            print(f"Ошибка в аудио-потоке: {e}")
        finally:
            print("Аудио-поток остановлен.")

    def start(self, device=None):
        if not device and not self.speaker:
            return False
        if device and not self.speaker:
            self.speaker = device
        self.running = True
        self.thread = th.Thread(target=self._device_worker, args=(self.speaker,))
        self.thread.start()
        return True

    def stop(self):
        if self.running:
            self.running = False
            if hasattr(self, 'thread'):
                self.thread.join()
                
    def change_mode(self): # 0, 1
        # 0 - режим миксера, 1 - режим одиночного звука как в soundpad
        self.mode = not self.mode
        
    def clear_sounds(self):
        self.active_sounds = []
        
    def change_pause(self):
        self.pause = not self.pause
        