#include "PhaserEffect.h"
#include "SynthUtils.h"

void PhaserEffect::prepare(const juce::dsp::ProcessSpec& spec)
{
    mPhaser.prepare(spec);
    mPhaser.setCentreFrequency(1000.f);
    mPhaser.setMix(1.f);
}

void PhaserEffect::reset() { mPhaser.reset(); }

void PhaserEffect::setParams(float rateNorm, float depth, float feedback)
{
    // rateNorm [0..1] → линейно 0.01..8 Гц
    const float rate = 0.01f + rateNorm * 7.99f;
    mPhaser.setRate(rate);
    mPhaser.setDepth(juce::jlimit(0.f, 1.f, depth));
    mPhaser.setFeedback(juce::jlimit(-0.95f, 0.95f, feedback * 0.95f));
}

void PhaserEffect::processBlock(juce::AudioBuffer<float>& buffer)
{
    auto block = juce::dsp::AudioBlock<float>(buffer);
    auto ctx   = juce::dsp::ProcessContextReplacing<float>(block);
    mPhaser.process(ctx);
}
