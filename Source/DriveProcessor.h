#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <vector>

// Tanh soft-clip overdrive with 1-pole LP tone control.
// drive=0 → clean pass-through; drive=1 → heavy saturation.
// tone=0  → dark/warm (~1.5 kHz LP); tone=1 → bright (minimal filtering).
// Output level is compensated to stay roughly consistent across drive settings.
class DriveProcessor
{
public:
    void prepare(const juce::dsp::ProcessSpec& spec)
    {
        mSampleRate = static_cast<float>(spec.sampleRate);
        const size_t numCh = static_cast<size_t>(spec.numChannels);
        mToneState.assign(numCh, 0.f);
        updateToneCoeff();
    }

    void reset()
    {
        std::fill(mToneState.begin(), mToneState.end(), 0.f);
    }

    void setDrive(float drive) noexcept
    {
        mDrive = juce::jlimit(0.f, 1.f, drive);
    }

    void setTone(float tone) noexcept
    {
        mTone = juce::jlimit(0.f, 1.f, tone);
        updateToneCoeff();
    }

    void processBlock(juce::AudioBuffer<float>& buffer)
    {
        if (mDrive < 1e-4f) return;

        // Input gain: 1x (drive=0) … 20x (drive=1)  — pushes signal into saturation
        const float inputGain   = 1.f + mDrive * 19.f;
        // Output compensation: keeps RMS roughly constant
        const float outputGain  = 1.f / (1.f + mDrive * 2.5f);

        const int numSamples = buffer.getNumSamples();
        const int numCh = juce::jmin(buffer.getNumChannels(),
                                     static_cast<int>(mToneState.size()));

        for (int ch = 0; ch < numCh; ++ch)
        {
            float* data    = buffer.getWritePointer(ch);
            float& lpState = mToneState[static_cast<size_t>(ch)];

            for (int i = 0; i < numSamples; ++i)
            {
                // Saturation
                float y = std::tanh(data[i] * inputGain) * outputGain;

                // Tone: 1-pole LP (state variable)
                // blend: tone=0 → pure LP (dark), tone=1 → original (bright)
                lpState += mToneCoeff * (y - lpState);
                y = lpState + mTone * (y - lpState);

                data[i] = y;
            }
        }
    }

private:
    void updateToneCoeff()
    {
        // LP cutoff interpolates 1.5 kHz (dark) … 15 kHz (bright)
        const float cutoffHz = 1500.f + mTone * 13500.f;
        const float w = 2.f * juce::MathConstants<float>::pi * cutoffHz / mSampleRate;
        mToneCoeff = w / (1.f + w);
    }

    float mSampleRate = 44100.f;
    float mDrive      = 0.f;
    float mTone       = 0.5f;
    float mToneCoeff  = 0.f;

    std::vector<float> mToneState;
};
