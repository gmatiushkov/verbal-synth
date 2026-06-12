#include "SynthFilter.h"

static constexpr float kButterworthQ = 0.7071f;

void SynthFilter::prepare(double sampleRate, int /*blockSize*/)
{
    mSampleRate = sampleRate;

    juce::dsp::ProcessSpec spec{ sampleRate, 1, 1 };

    mFilter.prepare(spec);
    mFilter.setType(juce::dsp::StateVariableTPTFilterType::lowpass);
    mFilter.setCutoffFrequency(18000.f);
    mFilter.setResonance(0.5f);

    mFilter2.prepare(spec);
    mFilter2.setType(juce::dsp::StateVariableTPTFilterType::lowpass);
    mFilter2.setCutoffFrequency(18000.f);
    mFilter2.setResonance(kButterworthQ);

    mCutoffSmoother.reset(sampleRate, 0.02);   // 20ms
    mCutoffSmoother.setCurrentAndTargetValue(18000.f);
}

void SynthFilter::reset()
{
    mFilter.reset();
    mFilter2.reset();
}

void SynthFilter::setParams(int type, float cutoffHz, float resonance)
{
    using T = juce::dsp::StateVariableTPTFilterType;
    const T types[] = { T::lowpass, T::bandpass, T::highpass };
    mType = juce::jlimit(0, 2, type);
    mFilter.setType(types[mType]);
    mFilter2.setType(types[mType]);

    const float q = 0.5f + resonance * 9.5f;
    if (std::abs(q - mResonance) > 1e-3f)
    {
        mFilter.setResonance(q);
        mResonance = q;
    }
    mFilter2.setResonance(kButterworthQ);

    mCutoffSmoother.setTargetValue(juce::jlimit(20.f, 18000.f, cutoffHz));
}

float SynthFilter::processSample(float input)
{
    const float cutHz = mCutoffSmoother.getNextValue();
    mFilter .setCutoffFrequency(cutHz);
    mFilter2.setCutoffFrequency(cutHz);
    return mFilter2.processSample(0, mFilter.processSample(0, input));
}

void SynthFilter::setTypeAndResonance(int type, float resonance)
{
    using T = juce::dsp::StateVariableTPTFilterType;
    const T types[] = { T::lowpass, T::bandpass, T::highpass };
    mType = juce::jlimit(0, 2, type);
    mFilter.setType(types[mType]);
    mFilter2.setType(types[mType]);

    const float q = 0.5f + resonance * 9.5f;
    if (std::abs(q - mResonance) > 1e-3f)
    {
        mFilter.setResonance(q);
        mResonance = q;
    }
    mFilter2.setResonance(kButterworthQ);
}

float SynthFilter::processSampleRaw(float input, float cutoffHz)
{
    const float clampedHz = juce::jlimit(20.f, 18000.f, cutoffHz);
    mFilter .setCutoffFrequency(clampedHz);
    mFilter2.setCutoffFrequency(clampedHz);
    return mFilter2.processSample(0, mFilter.processSample(0, input));
}
