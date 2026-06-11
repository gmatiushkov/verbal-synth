#pragma once
#include <juce_audio_basics/juce_audio_basics.h>
#include "SynthParameters.h"
#include "WavetableBank.h"
#include "WavetableOscillator.h"
#include "NoiseGenerator.h"
#include "SynthFilter.h"
#include "AdsrEnvelope.h"

class SynthVoice
{
public:
    void prepare(double sampleRate, int blockSize);
    void setBanks(const std::vector<WavetableBank>* banks);

    void noteOn(int midiNote, int velocity, const SynthPatch& patch);
    void noteOff();

    bool isActive() const;
    int getCurrentNote() const { return mNote; }

    void renderNextBlock(juce::AudioBuffer<float>& buffer,
                         int startSample, int numSamples,
                         const float* lfo1Vals, const float* lfo2Vals);

    void updatePatch(const SynthPatch& patch);

private:
    WavetableOscillator mOsc1, mOsc2;
    NoiseGenerator      mNoise;
    SynthFilter         mFilter;
    AdsrEnvelope        mAmpEnv, mFilterEnv;

    SynthPatch mPatch;
    const std::vector<WavetableBank>* mBanks = nullptr;

    int   mNote      = 60;
    float mVelocity  = 1.0f;
    bool  mNoteIsOn  = false;
    double mSampleRate = 44100.0;
    int    mBlockSize  = 512;

    std::vector<float> mMonoBuf;

    void updateOscBanks();
    float computeOsc1Freq() const;
    float computeOsc2Freq() const;
};
