#pragma once
#include "WavetableBank.h"
#include <cmath>

class WavetableOscillator
{
public:
    void prepare(double sampleRate)
    {
        mSampleRate = sampleRate;
        mPhase = 0.0;
        mPhaseDelta = 0.0;
    }

    void reset()
    {
        mPhase = 0.0;
    }

    void setBank(const WavetableBank* bank)
    {
        mBank = bank;
    }

    void setFrequency(float hz, double sampleRate)
    {
        mSampleRate = sampleRate;
        mPhaseDelta = static_cast<double>(hz) / sampleRate;
    }

    void setFrequency(float hz)
    {
        mPhaseDelta = static_cast<double>(hz) / mSampleRate;
    }

    void setPosition(float pos)
    {
        mPosition = juce::jlimit(0.f, 1.f, pos);
    }

    float getSample()
    {
        if (mBank == nullptr || mBank->numFrames == 0 || mBank->data.empty())
        {
            mPhase += mPhaseDelta;
            if (mPhase >= 1.0) mPhase -= 1.0;
            return 0.f;
        }

        const int numFrames = mBank->numFrames;

        // Frame interpolation
        const float fPos = mPosition * static_cast<float>(numFrames - 1);
        const int   fA   = static_cast<int>(fPos);
        const int   fB   = juce::jmin(fA + 1, numFrames - 1);
        const float fFrac = fPos - static_cast<float>(fA);

        const float* dataA = mBank->getFrame(fA);
        const float* dataB = mBank->getFrame(fB);

        // Phase interpolation within frame
        const double phaseF = mPhase * static_cast<double>(WavetableBank::kFrameSize);
        const int    idx0   = static_cast<int>(phaseF) % WavetableBank::kFrameSize;
        const int    idx1   = (idx0 + 1) % WavetableBank::kFrameSize;
        const float  pFrac  = static_cast<float>(phaseF - static_cast<double>(static_cast<int>(phaseF)));

        // Bilinear interpolation
        const float sA = dataA[idx0] + pFrac * (dataA[idx1] - dataA[idx0]);
        const float sB = dataB[idx0] + pFrac * (dataB[idx1] - dataB[idx0]);

        // Advance phase
        mPhase += mPhaseDelta;
        if (mPhase >= 1.0) mPhase -= 1.0;

        return sA + fFrac * (sB - sA);
    }

private:
    const WavetableBank* mBank = nullptr;
    double mPhase = 0.0;
    double mPhaseDelta = 0.0;
    float  mPosition = 0.f;
    double mSampleRate = 44100.0;
};
