#include "DelayEffect.h"
#include "SynthUtils.h"

void DelayEffect::prepare(const juce::dsp::ProcessSpec& spec)
{
    mSampleRate = spec.sampleRate;

    const int maxSamples = static_cast<int>(mSampleRate * kMaxDelaySeconds) + 1;
    mDelayL.prepare(spec);
    mDelayR.prepare(spec);
    mDelayL.setMaximumDelayInSamples(maxSamples);
    mDelayR.setMaximumDelayInSamples(maxSamples);

    mDelaySamples.reset(mSampleRate, 0.1);   // 100ms сглаживание смены времени
    mDelaySamples.setCurrentAndTargetValue(static_cast<float>(mSampleRate) * 0.3f);
}

void DelayEffect::reset()
{
    mDelayL.reset();
    mDelayR.reset();
}

void DelayEffect::setParams(float timeNorm, float feedback, float mix)
{
    const float timeSec = SynthUtils::logParam(timeNorm, 0.01f, 1.f);
    mDelaySamples.setTargetValue(static_cast<float>(mSampleRate) * timeSec);
    mFeedback = juce::jlimit(0.f, 0.95f, feedback);
    mMix      = juce::jlimit(0.f, 1.f, mix);
}

void DelayEffect::processBlock(juce::AudioBuffer<float>& buffer)
{
    if (mMix < 1e-4f) return;

    const int numSamples = buffer.getNumSamples();
    const int numCh      = buffer.getNumChannels();

    for (int i = 0; i < numSamples; ++i)
    {
        const float delaySamples = mDelaySamples.getNextValue();

        if (numCh >= 1)
        {
            float* chL = buffer.getWritePointer(0);
            const float wet = mDelayL.popSample(0, delaySamples);
            mDelayL.pushSample(0, chL[i] + wet * mFeedback);
            chL[i] = chL[i] * (1.f - mMix) + wet * mMix;
        }
        if (numCh >= 2)
        {
            float* chR = buffer.getWritePointer(1);
            const float wet = mDelayR.popSample(0, delaySamples);
            mDelayR.pushSample(0, chR[i] + wet * mFeedback);
            chR[i] = chR[i] * (1.f - mMix) + wet * mMix;
        }
    }
}
