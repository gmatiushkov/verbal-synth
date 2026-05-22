#include "ReverbEffect.h"

void ReverbEffect::prepare(const juce::dsp::ProcessSpec& spec)
{
    mReverb.prepare(spec);
}

void ReverbEffect::reset()
{
    mReverb.reset();
}

void ReverbEffect::setParams(float time, float damp, float mix)
{
    juce::dsp::Reverb::Parameters p;
    p.roomSize   = juce::jlimit(0.f, 1.f, time);
    p.damping    = juce::jlimit(0.f, 1.f, damp);
    p.wetLevel   = juce::jlimit(0.f, 1.f, mix);
    p.dryLevel   = 1.f - p.wetLevel;
    p.width      = 1.f;
    p.freezeMode = 0.f;
    mReverb.setParameters(p);
}

void ReverbEffect::processBlock(juce::AudioBuffer<float>& buffer)
{
    auto block = juce::dsp::AudioBlock<float>(buffer);
    auto ctx   = juce::dsp::ProcessContextReplacing<float>(block);
    mReverb.process(ctx);
}
