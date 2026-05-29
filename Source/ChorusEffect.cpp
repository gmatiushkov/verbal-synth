#include "ChorusEffect.h"

void ChorusEffect::prepare(const juce::dsp::ProcessSpec& spec)
{
    mChorus.prepare(spec);
}

void ChorusEffect::reset()
{
    mChorus.reset();
}

void ChorusEffect::setParams(float rate, float depth, float mix)
{
    mChorus.setRate(0.1f + rate * 4.9f);
    mChorus.setDepth(depth * 0.015f);
    mChorus.setMix(mix);
    mChorus.setCentreDelay(7.f);
    mChorus.setFeedback(0.f);
}

void ChorusEffect::processBlock(juce::AudioBuffer<float>& buffer)
{
    juce::dsp::AudioBlock<float> block(buffer);
    juce::dsp::ProcessContextReplacing<float> ctx(block);
    mChorus.process(ctx);
}
