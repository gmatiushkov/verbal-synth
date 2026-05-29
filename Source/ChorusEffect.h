#pragma once
#include <juce_dsp/juce_dsp.h>

class ChorusEffect
{
public:
    void prepare(const juce::dsp::ProcessSpec& spec);
    void reset();

    // rate [0,1]→0.1..5Hz, depth [0,1], mix [0,1]
    void setParams(float rate, float depth, float mix);

    void processBlock(juce::AudioBuffer<float>& buffer);

private:
    juce::dsp::Chorus<float> mChorus;
};
