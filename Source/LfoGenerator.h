#pragma once
#include <juce_dsp/juce_dsp.h>

// LFO с тем же морфингом форм волны, что и Oscillator.
// Возвращает значение [-1..1] на каждый вызов getNextSample().
class LfoGenerator
{
public:
    void prepare(double sampleRate);
    void reset();

    // rateNorm [0..1] → 0.01..20 Гц (логарифмически)
    // shapeMorph [0..1]: 0=sine, 0.25=tri, 0.5=saw, 0.75=rsaw, 1=square
    void setParams(float rateNorm, float shapeMorph);

    float getNextSample();

private:
    juce::dsp::Oscillator<float> mSine, mTri, mSaw, mSquare;

    float  mMorph      = 0.f;
    double mSampleRate = 44100.0;

    // Slew limiter: prevents audible clicks at saw/square discontinuities
    float mSlewPrev  = 0.f;
    float mSlewLimit = 0.023f;  // updated in prepare()

    void syncRate(float hz);

    static float blend(float morph, float lo, float hi)
    {
        return (morph - lo) / (hi - lo);
    }
};
