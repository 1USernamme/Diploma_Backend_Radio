import numpy as np
import io
from scipy.fft import fft, fftfreq
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import EmailTokenObtainPairSerializer, RegisterSerializer


@api_view(["POST"])
def analyze_signal(request):
    """
    Науково обґрунтований аналіз ефіру з динамічним розрахунком SNR
    та пороговим виявленням радіоелектронних загроз.
    """

    freq = float(request.data.get("frequency", 25.0))
    np.random.seed(42)
    noise_lvl = float(request.data.get("noise_level", 0.3))
    sr = int(request.data.get("sampling_rate", 500))
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Моделюємо ситуацію: якщо частота менше 5 Гц — вважаємо, що передавач вимкнено (чистий ефір)
    if freq < 5:
        signal_with_noise = np.random.normal(0, noise_lvl, size=t.shape)
    else:
        # Корисний сигнал РЕЗ
        clean_signal = np.sin(2 * np.pi * freq * t)
        # Адитивний білий гаусів шум (AWGN)
        noise = np.random.normal(0, noise_lvl, size=t.shape)
        signal_with_noise = clean_signal + noise

    # Швидке перетворення Фур'є (FFT)
    n = len(t)
    yf = fft(signal_with_noise)
    xf = fftfreq(n, 1 / sr)

    half_n = n // 2
    frequencies = xf[:half_n].tolist()
    amplitudes = (2.0 / n * np.abs(yf[:half_n])).tolist()

    # --- НАУКОВА ЛОГІКА ВИЯВЛЕННЯ ЗАГРОЗИ ---
    max_amplitude = float(max(amplitudes))
    detected_freq = float(frequencies[amplitudes.index(max_amplitude)])

    # Рахуємо середній рівень шуму в ефірі (все, що не є піком)
    average_noise = float(np.mean(amplitudes))

    # Розрахунок відношення сигнал/шум (SNR) в децибелах (dB)
    # Якщо ефір порожній, SNR буде в районі 0 або мінусовим
    if average_noise > 0 and max_amplitude > average_noise:
        snr = 20 * np.log10(max_amplitude / average_noise)
    else:
        snr = 0.0

    # Критерій виявлення загрози:
    # Пік має бути мінімум у 3.5 рази вищим за середній шум, і частота має бути реальною (> 0)
    is_threat = (max_amplitude > (average_noise * 3.5)) and detected_freq > 0

    return Response(
        {
            "time": t.tolist(),
            "signal": signal_with_noise.tolist(),
            "frequencies": frequencies,
            "amplitudes": amplitudes,
            "metrics": {
                "max_amplitude": round(max_amplitude, 3),
                "detected_frequency": round(detected_freq, 2) if is_threat else 0.0,
                "average_noise_floor": round(average_noise, 3),
                "snr_db": round(float(snr), 2),
                "is_threat": bool(is_threat),  # Приводимо до стандартного bool для JSON
            },
        }
    )


@api_view(["POST"])
def analyze_uploaded_file(request):
    """
    Ендпоінт для прийому файлу з відліками SDR та проведення спектрального аналізу.
    Очікується файл (.csv або .txt) де кожне число - це амплітуда в новий момент часу.
    """
    file_obj = request.FILES.get("file")
    sr = int(request.data.get("sampling_rate", 500))

    if not file_obj:
        return Response({"error": "Файл не надано"}, status=400)

    try:
        # Читаємо файл прямо з пам'яті
        file_content = file_obj.read().decode("utf-8")

        # Перетворюємо текст на numpy масив (припускаємо, що це стовпчик чисел)
        # Якщо в файлі числа розділені комами або пробілами, numpy з цим впорається
        signal_data = np.loadtxt(io.StringIO(file_content), delimiter=",")

        # Якщо раптом файл багатовимірний (наприклад I та Q канали), беремо лише перший (або рахуємо магнітуду)
        if signal_data.ndim > 1:
            signal_data = signal_data[:, 0]

    except Exception as e:
        return Response({"error": f"Помилка читання файлу: {str(e)}"}, status=400)

    n = len(signal_data)
    if n == 0:
        return Response({"error": "Файл порожній"}, status=400)

    # Генеруємо часову вісь для графіку (duration = кількість точок / частоту дискретизації)
    duration = n / sr
    t = np.linspace(0, duration, n, endpoint=False)

    # Робимо FFT
    yf = fft(signal_data)
    xf = fftfreq(n, 1 / sr)

    half_n = n // 2
    frequencies = xf[:half_n].tolist()
    amplitudes = (2.0 / n * np.abs(yf[:half_n])).tolist()

    # Аналітика та пошук загроз (та сама наукова логіка)
    max_amplitude = float(max(amplitudes))
    detected_freq = float(frequencies[amplitudes.index(max_amplitude)])
    average_noise = float(np.mean(amplitudes))

    if average_noise > 0 and max_amplitude > average_noise:
        snr = 20 * np.log10(max_amplitude / average_noise)
    else:
        snr = 0.0

    is_threat = (max_amplitude > (average_noise * 3.5)) and detected_freq > 0

    return Response(
        {
            "time": t.tolist(),
            "signal": signal_data.tolist(),
            "frequencies": frequencies,
            "amplitudes": amplitudes,
            "metrics": {
                "max_amplitude": round(max_amplitude, 3),
                "detected_frequency": round(detected_freq, 2) if is_threat else 0.0,
                "average_noise_floor": round(average_noise, 3),
                "snr_db": round(float(snr), 2),
                "is_threat": bool(is_threat),
            },
        }
    )


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            serializer.to_representation(user),
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = EmailTokenObtainPairSerializer
