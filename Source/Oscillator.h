#pragma once
#include <juce_dsp/juce_dsp.h>

// Морфирующий осциллятор: sine → triangle → saw → square.
// morph [0..1]: 0=sine, 0.33=tri, 0.67=saw, 1=square
class Oscillator
{
public:
    void prepare(double sampleRate, int blockSize);
    void reset();

    // force=true sets frequency immediately (no smoothing) — use on noteOn
    void setFrequency(float hz, bool force = false);

    void setMorph(float morph);

    float renderSample();

private:
    juce::dsp::Oscillator<float> mSine, mTri, mSaw, mSquare;

    float  mMorph      = 0.5f;
    float  mFrequency  = 440.f;
    double mSampleRate = 44100.0;

    void syncFrequency(bool force);

    // Коэффициент смешивания для морфа внутри сегмента [lo..hi]
    static float blend(float morph, float lo, float hi)
    {
        return (morph - lo) / (hi - lo);
    }
};
