#include "Oscillator.h"
#include <juce_core/juce_core.h>

static constexpr int kLutSize = 256;

void Oscillator::prepare(double sampleRate, int /*blockSize*/)
{
    mSampleRate = sampleRate;

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

    syncFrequency(false);
}

void Oscillator::reset()
{
    mSine  .reset();
    mTri   .reset();
    mSaw   .reset();
    mSquare.reset();
}

void Oscillator::setFrequency(float hz, bool force)
{
    mFrequency = hz;
    syncFrequency(force);
}

void Oscillator::setMorph(float morph)
{
    mMorph = juce::jlimit(0.f, 1.f, morph);
}

float Oscillator::renderSample()
{
    const float s = mSine  .processSample(0.f);
    const float t = mTri   .processSample(0.f);
    const float w = mSaw   .processSample(0.f);
    const float q = mSquare.processSample(0.f);

    // 3 segments: [0..0.333] [0.333..0.667] [0.667..1.0]
    if (mMorph < 0.333f)
    {
        const float b = blend(mMorph, 0.f, 0.333f);
        return s * (1.f - b) + t * b;
    }
    else if (mMorph < 0.667f)
    {
        const float b = blend(mMorph, 0.333f, 0.667f);
        return t * (1.f - b) + w * b;
    }
    else
    {
        const float b = blend(mMorph, 0.667f, 1.f);
        return w * (1.f - b) + q * b;
    }
}

void Oscillator::syncFrequency(bool force)
{
    const float hz = juce::jlimit(10.f, 20000.f, mFrequency);
    mSine  .setFrequency(hz, force);
    mTri   .setFrequency(hz, force);
    mSaw   .setFrequency(hz, force);
    mSquare.setFrequency(hz, force);
}
