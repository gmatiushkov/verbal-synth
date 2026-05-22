#pragma once
#include <juce_dsp/juce_dsp.h>

class ReverbEffect
{
public:
    void prepare(const juce::dsp::ProcessSpec& spec);
    void reset();
    void setParams(float time, float damp, float mix);
    void processBlock(juce::AudioBuffer<float>& buffer);

private:
    juce::dsp::Reverb mReverb;
};
