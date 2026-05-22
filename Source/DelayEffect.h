#pragma once
#include <juce_dsp/juce_dsp.h>

class DelayEffect
{
public:
    void prepare(const juce::dsp::ProcessSpec& spec);
    void reset();
    // timeNorm [0..1] → 10ms..1s  |  feedback [0..1]  |  mix [0..1]
    void setParams(float timeNorm, float feedback, float mix);
    void processBlock(juce::AudioBuffer<float>& buffer);

private:
    static constexpr float kMaxDelaySeconds = 1.f;

    juce::dsp::DelayLine<float, juce::dsp::DelayLineInterpolationTypes::Linear> mDelayL, mDelayR;
    juce::SmoothedValue<float> mDelaySamples;

    float  mFeedback   = 0.3f;
    float  mMix        = 0.f;
    double mSampleRate = 44100.0;
};
