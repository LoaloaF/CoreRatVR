import numpy as np
import matplotlib.pyplot as plt

# Parameters
frequency = 50  # Hz
burst_duration = 400e-3  # seconds
burst_interval = 1 / frequency  # seconds
pulse_duration = 167e-6  # seconds per phase
inter_phase_interval = 67e-6  # seconds
amplitudes = [2, 5, 7, 10]  # microamperes

# Derived parameters
pulse_period = 1 / frequency  # seconds per pulse
n_pulses = int(burst_duration / pulse_period)  # number of pulses per burst

def generate_pulse_train(amplitude, dt):
    """
    Generate a biphasic pulse train for one burst.
    """
    t = np.arange(0, burst_duration, dt)
    signal = np.zeros_like(t)

    for i in range(n_pulses):
        start_idx = int(i * pulse_period / dt)
        # Cathodic phase
        end_cathodic = start_idx + int(pulse_duration / dt)
        signal[start_idx:end_cathodic] = -amplitude

        # Inter-phase interval
        end_inter_phase = end_cathodic + int(inter_phase_interval / dt)

        # Anodic phase
        end_anodic = end_inter_phase + int(pulse_duration / dt)
        signal[end_inter_phase:end_anodic] = amplitude

    return t, signal

# Time settings for plotting
duration = 2  # seconds of total simulation time
dt = 1e-6  # time resolution

t = np.arange(0, duration, dt)
signal = np.zeros_like(t)

# Generate the pulse train for one amplitude
chosen_amplitude = amplitudes[2]  # Use the largest amplitude (10 microamperes)
burst_start = 0
while burst_start < duration:
    t_burst, burst_signal = generate_pulse_train(chosen_amplitude, dt)
    burst_length = len(np.logical_and(t >= burst_start, t < burst_start + burst_duration).nonzero()[0])
    signal_slice = burst_signal[:burst_length]  # Ensure matching length
    signal[np.logical_and(t >= burst_start, t < burst_start + burst_duration)] = signal_slice
    burst_start += burst_interval

# Plotting
plt.figure(figsize=(12, 6))
plt.plot(t * 1e3, signal, label=f"Amplitude: {chosen_amplitude} μA")
plt.title("Electrical Stimulation Profile")
plt.xlabel("Time (ms)")
plt.ylabel("Current (μA)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
