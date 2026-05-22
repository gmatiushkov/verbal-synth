#pragma once
#include <juce_dsp/juce_dsp.h>

// Mono TPT state-variable filter (LP/BP/HP).
// cutoff плавно сглаживается через SmoothedValue.
class SynthFilter
{
public:
    void prepare(double sampleRate, int blockSize);
    void reset();

    // type: 0=LP, 1=BP, 2=HP  |  cutoffHz уже в Гц  |  resonance [0..1] → Q [0.5..10]
    void setParams(int type, float cutoffHz, float resonance);

    float processSample(float input);

    void snapToZero() { mFilter.snapToZero(); }

private:
    juce::dsp::StateVariableTPTFilter<float> mFilter;
    juce::SmoothedValue<float, juce::ValueSmoothingTypes::Multiplicative> mCutoffSmoother;

    double mSampleRate = 44100.0;
    int    mType       = 0;
    float  mResonance  = 0.5f;
};
