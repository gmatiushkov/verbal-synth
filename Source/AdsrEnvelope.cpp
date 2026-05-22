#include "AdsrEnvelope.h"
#include <cmath>

void AdsrEnvelope::prepare(double sampleRate)
{
    mAdsr.setSampleRate(sampleRate);
}

void AdsrEnvelope::reset()
{
    mAdsr.reset();
}

void AdsrEnvelope::applyParams(float attack, float decay, float sustain, float release)
{
    mParams.attack  = logTime(attack,  0.0005f, 5.f);
    mParams.decay   = logTime(decay,   0.001f,  5.f);
    mParams.sustain = sustain;
    mParams.release = logTime(release, 0.005f,  10.f);
    mAdsr.setParameters(mParams);
}

void AdsrEnvelope::noteOn()  { mAdsr.noteOn();  }
void AdsrEnvelope::noteOff() { mAdsr.noteOff(); }

void AdsrEnvelope::applyToBlock(float* samples, int numSamples)
{
    for (int i = 0; i < numSamples; ++i)
        samples[i] *= mAdsr.getNextSample();
}

float AdsrEnvelope::logTime(float norm, float minSec, float maxSec)
{
    return minSec * std::pow(maxSec / minSec, norm);
}
