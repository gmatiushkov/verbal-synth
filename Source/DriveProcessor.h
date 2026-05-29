#pragma once
#include <juce_dsp/juce_dsp.h>
#include <cmath>
#include <vector>

// Tanh soft-clip overdrive with 1-pole LP tone control.
// drive=0  → bypass (clean)
// drive=0.2 → light crunch  (inputGain ~2.3x)
// drive=0.5 → overdrive     (inputGain ~6.3x)
// drive=1.0 → hard distortion (inputGain 40x)
//
// Volume compensation: output is calibrated to keep the perceived level
// approximately constant for a reference amplitude of 0.35 (typical post-voice mix).
// Formula: outputGain = 0.35 / tanh(0.35 * inputGain)
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

        // Exponential gain curve: 1x (clean) → 40x (brutal) via pow(40, drive)
        const float inputGain  = std::pow(40.f, mDrive);
        // Exact volume compensation matched to reference amplitude 0.35
        const float kRef       = 0.35f;
        const float outputGain = kRef / std::tanh(kRef * inputGain);

        const int numSamples = buffer.getNumSamples();
        const int numCh = juce::jmin(buffer.getNumChannels(),
                                     static_cast<int>(mToneState.size()));

        for (int ch = 0; ch < numCh; ++ch)
        {
            float* data    = buffer.getWritePointer(ch);
            float& lpState = mToneState[static_cast<size_t>(ch)];

            for (int i = 0; i < numSamples; ++i)
            {
                float y = std::tanh(data[i] * inputGain) * outputGain;

                // Tone: 1-pole LP blend — tone=0 dark (~1.5 kHz), tone=1 bright
                lpState += mToneCoeff * (y - lpState);
                y = lpState + mTone * (y - lpState);

                data[i] = y;
            }
        }
    }

private:
    void updateToneCoeff()
    {
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
