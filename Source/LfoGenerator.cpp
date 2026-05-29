#include "LfoGenerator.h"
#include "SynthUtils.h"
#include <juce_core/juce_core.h>

static constexpr int kLutSize = 256;

void LfoGenerator::prepare(double sampleRate)
{
    mSampleRate = sampleRate;
    // Allow full [-1,1] swing in 2 ms — removes saw/square click without affecting shape
    mSlewLimit = 2.f / (static_cast<float>(sampleRate) * 0.002f);
    mSlewPrev  = 0.f;

    mSine  .initialise([](float x){ return std::sin(x); }, kLutSize);
    mTri   .initialise([](float x){
        return x < 0.f ? (x / juce::MathConstants<float>::pi + 1.f) * 2.f - 1.f
                       : 1.f - (x / juce::MathConstants<float>::pi) * 2.f;
    }, kLutSize);
    mSaw   .initialise([](float x){ return x / juce::MathConstants<float>::pi; }, kLutSize);
    mSquare.initialise([](float x){ return x < 0.f ? -1.f : 1.f; }, kLutSize);

    juce::dsp::ProcessSpec spec{ sampleRate, 1, 1 };
    mSine  .prepare(spec);
    mTri   .prepare(spec);
    mSaw   .prepare(spec);
    mSquare.prepare(spec);

    syncRate(1.f);
}

void LfoGenerator::reset()
{
    mSine  .reset();
    mTri   .reset();
    mSaw   .reset();
    mSquare.reset();
    mSlewPrev = 0.f;
}

void LfoGenerator::setParams(float rateNorm, float shapeMorph)
{
    mMorph = juce::jlimit(0.f, 1.f, shapeMorph);
    syncRate(SynthUtils::logParam(rateNorm, 0.01f, 20.f));
}

float LfoGenerator::getNextSample()
{
    const float s = mSine  .processSample(0.f);
    const float t = mTri   .processSample(0.f);
    const float w = mSaw   .processSample(0.f);
    const float q = mSquare.processSample(0.f);

    float raw;
    if (mMorph < 0.333f)
    {
        const float b = blend(mMorph, 0.f, 0.333f);
        raw = s * (1.f - b) + t * b;
    }
    else if (mMorph < 0.667f)
    {
        const float b = blend(mMorph, 0.333f, 0.667f);
        raw = t * (1.f - b) + w * b;
    }
    else
    {
        const float b = blend(mMorph, 0.667f, 1.f);
        raw = w * (1.f - b) + q * b;
    }

    // Slew limiter: caps rate-of-change to remove clicks at wave discontinuities
    const float delta  = raw - mSlewPrev;
    const float slewed = mSlewPrev + juce::jlimit(-mSlewLimit, mSlewLimit, delta);
    mSlewPrev = slewed;
    return slewed;
}

void LfoGenerator::syncRate(float hz)
{
    const float rate = juce::jlimit(0.01f, 20.f, hz);
    mSine  .setFrequency(rate);
    mTri   .setFrequency(rate);
    mSaw   .setFrequency(rate);
    mSquare.setFrequency(rate);
}
