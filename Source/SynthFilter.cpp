#include "SynthFilter.h"

void SynthFilter::prepare(double sampleRate, int /*blockSize*/)
{
    mSampleRate = sampleRate;

    juce::dsp::ProcessSpec spec{ sampleRate, 1, 1 };
    mFilter.prepare(spec);
    mFilter.setType(juce::dsp::StateVariableTPTFilterType::lowpass);
    mFilter.setCutoffFrequency(18000.f);
    mFilter.setResonance(0.5f);

    mCutoffSmoother.reset(sampleRate, 0.02);   // 20ms
    mCutoffSmoother.setCurrentAndTargetValue(18000.f);
}

void SynthFilter::reset()
{
    mFilter.reset();
}

void SynthFilter::setParams(int type, float cutoffHz, float resonance)
{
    using T = juce::dsp::StateVariableTPTFilterType;
    const T types[] = { T::lowpass, T::bandpass, T::highpass };
    mType = juce::jlimit(0, 2, type);
    mFilter.setType(types[mType]);

    const float q = 0.5f + resonance * 9.5f;
    if (std::abs(q - mResonance) > 1e-3f)
    {
        mFilter.setResonance(q);
        mResonance = q;
    }

    mCutoffSmoother.setTargetValue(juce::jlimit(20.f, 18000.f, cutoffHz));
}

float SynthFilter::processSample(float input)
{
    mFilter.setCutoffFrequency(mCutoffSmoother.getNextValue());
    return mFilter.processSample(0, input);
}

void SynthFilter::setTypeAndResonance(int type, float resonance)
{
    using T = juce::dsp::StateVariableTPTFilterType;
    const T types[] = { T::lowpass, T::bandpass, T::highpass };
    mType = juce::jlimit(0, 2, type);
    mFilter.setType(types[mType]);

    const float q = 0.5f + resonance * 9.5f;
    if (std::abs(q - mResonance) > 1e-3f)
    {
        mFilter.setResonance(q);
        mResonance = q;
    }
}

float SynthFilter::processSampleRaw(float input, float cutoffHz)
{
    mFilter.setCutoffFrequency(juce::jlimit(20.f, 18000.f, cutoffHz));
    return mFilter.processSample(0, input);
}
