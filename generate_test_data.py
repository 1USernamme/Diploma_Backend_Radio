import numpy as np
import csv


def generate_csv():
    # Налаштування нашого тестового радіоефіру
    sr = 500  # Частота дискретизації (Гц)
    duration = 2.0  # Тривалість запису (секунди) - загалом буде 1000 відліків
    target_freq = 42.0  # Зімітуємо ворожий сигнал на частоті 42 Гц
    noise_level = 0.6  # Додамо трохи реалістичного білого шуму

    print(f"Генерація сигналу: частота {target_freq} Гц, шум {noise_level}...")

    # Математика генерації
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    clean_signal = np.sin(2 * np.pi * target_freq * t)
    noise = np.random.normal(0, noise_level, size=t.shape)
    final_signal = clean_signal + noise

    # Збереження у файл
    filename = "test_signal.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        for value in final_signal:
            # Записуємо кожне значення з точністю до 6 знаків
            writer.writerow([round(value, 6)])

    print(f"✅ Готово! Файл {filename} успішно створено поруч із цим скриптом.")
    print("Тепер ти можеш завантажити його через веб-інтерфейс.")


if __name__ == "__main__":
    generate_csv()
