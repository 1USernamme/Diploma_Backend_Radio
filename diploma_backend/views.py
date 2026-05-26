import numpy as np
from scipy.fft import fft, fftfreq
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def analyze_signal(request):
    """
    Ендпоінт для генерації сигналу, додавання шуму та проведення FFT.
    Приймає параметри: frequency, noise_level, sampling_rate, signal_type
    """
    # Отримуємо параметри з фронтенду або ставимо дефолтні
    freq = float(request.data.get('frequency', 10.0))         # Частота корисного сигналу (Гц)
    noise_lvl = float(request.data.get('noise_level', 0.5))    # Амплітуда шуму
    sr = int(request.data.get('sampling_rate', 500))           # Частота дискретизації (Гц)
    duration = 2.0                                             # Тривалість сигналу в секундах

    # 1. Генерація часової осі та чистого сигналу
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    # Можна розширювати типи сигналів (загроза / простий тон тощо)
    clean_signal = np.sin(2 * np.pi * freq * t)

    # 2. Моделювання завади (Адитивний білий гаусів шум)
    noise = np.random.normal(0, noise_lvl, size=t.shape)
    signal_with_noise = clean_signal + noise

    # 3. Спектральний аналіз за допомогою FFT (Швидке перетворення Фур'є)
    n = len(t)
    yf = fft(signal_with_noise)
    xf = fftfreq(n, 1 / sr)

    # Беремо тільки позитивні частоти (першу половину спектра)
    half_n = n // 2
    frequencies = xf[:half_n].tolist()
    # Обчислюємо амплітудний спектр
    amplitudes = (2.0 / n * np.abs(yf[:half_n])).tolist()

    # 4. Простий пороговий класифікатор загроз
    # Якщо амплітуда піку вища за 0.7 — вважаємо сигнал стабільною радіозагрозою
    max_amplitude = max(amplitudes)
    detected_freq = frequencies[amplitudes.index(max_amplitude)]
    is_threat = max_amplitude > 0.7 and detected_freq > 0

    return Response({
        'time': t.tolist(),
        'signal': signal_with_noise.tolist(),
        'frequencies': frequencies,
        'amplitudes': amplitudes,
        'metrics': {
            'max_amplitude': round(max_amplitude, 3),
            'detected_frequency': round(detected_freq, 2),
            'is_threat': is_threat
        }
    })