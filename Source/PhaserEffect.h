#pragma once
#include <juce_dsp/juce_dsp.h>

class PhaserEffect
{
public:
    void prepare(const juce::dsp::ProcessSpec& spec);
    void reset();
    void setParams(float rateNorm, float depth, float feedback);
    void processBlock(juce::AudioBuffer<float>& buffer);

private:
    juce::dsp::Phaser<float> mPhaser;
};
