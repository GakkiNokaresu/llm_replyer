import pyaudio
import wave
import threading

input_device_proposals = ["立体声混音", "Line 1", "cable", "Stereo mix"]


def get_input_devices():
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        devices.append(dev_info['name'])
    return devices


# 定义录音参数
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "output.wav"


class Recording:
    input_device_index = None
    p = pyaudio.PyAudio()
    stop_flag = False
    callback = None

    def __init__(self):
        pass

    def set_input_device(self, input_device_name):
        p = self.p
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0 and input_device_name.lower() in dev_info['name'].lower():
                self.input_device_index = i
                return True
        return False

    threadLock = threading.Lock()

    def stop(self):
        self.stop_flag = True

    def record(self, callback):
        # 尝试获取锁
        acquired = self.threadLock.acquire(timeout=0.1)  # 设置超时时间为1秒
        success = False

        if acquired:
            try:
                self.callback = callback
                self.__record()
                success = True
            finally:
                self.threadLock.release()
                return 1 if success else -1
        else:
            return 0

    def __record(self):
        if self.input_device_index is None:
            raise Exception("* 未设置音源")
        p = self.p
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=self.input_device_index,
                        frames_per_buffer=CHUNK)

        print("* 开始录制系统声音...")

        frames = []

        # 录制指定时长的音频数据
        count = 0
        while not self.stop_flag:
            data = stream.read(CHUNK)
            frames.append(data)
            count = count + 1
            if count >= RATE / CHUNK * 5:
                self.stop_flag = True

        # 关闭音频流
        stream.stop_stream()
        stream.close()
        p.terminate()

        # 将录制的音频数据保存为 WAV 文件
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        self.callback()
        print("* 录制完成")
