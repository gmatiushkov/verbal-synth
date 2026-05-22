#pragma once
#include <cmath>

namespace SynthUtils
{
    // norm [0..1] → логарифмическая интерполяция между minVal и maxVal
    inline float logParam(float norm, float minVal, float maxVal)
    {
        return minVal * std::pow(maxVal / minVal, norm);
    }

    // MIDI-нота → частота в Гц
    inline float midiToHz(int note)
    {
        return 440.f * std::pow(2.f, (note - 69) / 12.f);
    }

    // osc_octave [0..1] → целочисленный сдвиг октавы [-2..+2]
    inline int octaveShift(float norm)
    {
        return static_cast<int>(std::round(norm * 4.f)) - 2;
    }

    // osc_detune [0..1] → центы [-50..+50]
    inline float detuneInCents(float norm)
    {
        return (norm - 0.5f) * 100.f;
    }

    // центы → множитель частоты
    inline float centsToRatio(float cents)
    {
        return std::pow(2.f, cents / 1200.f);
    }

    // filter_type [0..1] → индекс 0=LP, 1=BP, 2=HP (ближайший)
    inline int filterTypeIndex(float norm)
    {
        if (norm < 0.25f) return 0;
        if (norm < 0.75f) return 1;
        return 2;
    }

    // Soft-clip через tanh: gain = 1 + drive*15, нормализован
    inline float softClip(float x, float drive)
    {
        const float gain = 1.f + drive * 15.f;
        const float denom = std::tanh(gain);
        return denom > 1e-6f ? std::tanh(x * gain) / denom : x;
    }
}
