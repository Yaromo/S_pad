import subprocess
import time
import json


def create_pipewire_cable(sink_name='Mixer_Audio_Sender', source_name='My_Virtual_Microphone', sink_name2='Music_Sender'):
    # Запускаем pw-loopback как отдельный процесс
    # Мы создаем устройство
    cmd = [
        "pw-loopback",
        "--capture-props", f"node.description={sink_name} node.name=p_sender media.class=Audio/Sink",
        "--playback-props", f"node.description={source_name} node.name=p_input media.class=Audio/Source"
    ]
    # Динамик на который выводится проигрывающиеся звуки
    cmd2 = [
        "pw-loopback",
        "--capture-props", f'node.description={sink_name2} node.name=m_sender media.class=Audio/Sink',
        "--playback-props", "node.target=p_sender"
        ]
    # Запускаем процесс в фоновом режиме
    
    process = subprocess.Popen(cmd)
    process2 = subprocess.Popen(cmd2)
    
    # Даем системе секунду, чтобы "увидеть" новое устройство
    time.sleep(0.5)
    return process, process2, sink_name, sink_name2


def connect_to_cable(sender_name, cable_name="p_sender", mono=True, mic=True):
    channels = ["FL", "FR"]
    mod = 'capture' if mic else 'monitor'
    for ch in channels:
        if mono:
            source = f"{sender_name}:{mod}_MONO"
        else:
            source = f"{sender_name}:{mod}_{ch}"
        sink = f"{cable_name}:playback_{ch}"
        subprocess.run(['pw-link', source, sink])


def get_microphone_name(search_term="analog-stereo", source=True):
    # Вызываем pw-dump для получения всех узлов в формате JSON
    result = subprocess.run(['pw-dump'], capture_output=True, text=True)
    data = json.loads(result.stdout)
    m_class = f"Audio/{'Source' if source else 'Sink'}"
    mod = 'input' if source else 'output'
    for obj in data:
        # Ищем объекты, которые являются аудио-источниками (микрофонами)
        if obj.get('type') == 'PipeWire:Interface:Node':
            props = obj.get('info', {}).get('props', {})
            media_class = props.get('media.class')
            
            # Проверяем, что это источник звука (Audio/Source)
            if media_class == m_class:
                name = props.get('node.name')
                description = props.get('node.description', '')
                # Фильтруем по ключевому слову (например, 'USB' или 'analog')
                if (search_term.lower() in name.lower() or search_term.lower() in description.lower()):
                    return name
    return None


def disconnect_cable(sender_name, cable_name="p_sender", mono=True, mic=True):
    channels = ["FL", "FR"]
    mod = 'capture' if mic else 'monitor'
    for ch in channels:
        if mono:
            # Некоторые устройства используют просто 'MONO', некоторые 'mono'
            sources = [f"{sender_name}:{mod}_MONO", f"{sender_name}:{mod}_mono"]
        else:
            sources = [f"{sender_name}:{mod}_{ch}"]
            
        sink = f"{cable_name}:playback_{ch}"
        
        # Перебираем возможные варианты имен портов источника
        for source in sources:
            # stderr=subprocess.DEVNULL скроет лишний спам об ошибках в консоли,
            # если мы перебираем имена портов и угадываем нужное
            result = subprocess.run(
                ['pw-link', '-d', source, sink], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            # Если отключение прошло успешно (returncode == 0), прерываем внутренний цикл
            if result.returncode == 0:
                break
