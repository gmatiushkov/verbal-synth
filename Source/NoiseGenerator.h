#pragma once
#include <juce_audio_basics/juce_audio_basics.h>

class NoiseGenerator
{
public:
    void prepare(double /*sampleRate*/) { mRandom.setSeedRandomly(); }
    void reset() {}

    float getSample() noexcept
    {
        return mRandom.nextFloat() * 2.f - 1.f;
    }

    void renderAdd(float* dst, int numSamples, float level) noexcept
    {
        if (level < 1e-5f) return;
        for (int i = 0; i < numSamples; ++i)
            dst[i] += getSample() * level;
    }

private:
    juce::Random mRandom;
};
