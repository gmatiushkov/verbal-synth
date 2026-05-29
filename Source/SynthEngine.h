#pragma once
#include <array>
#include <atomic>
#include <vector>
#include <juce_audio_basics/juce_audio_basics.h>
#include <juce_dsp/juce_dsp.h>
#include "SynthParameters.h"
#include "WavetableBank.h"
#include "SynthVoice.h"
#include "LfoGenerator.h"
#include "DriveProcessor.h"
#include "ReverbEffect.h"

class SynthEngine
{
public:
    SynthEngine();

    void prepare(double sampleRate, int samplesPerBlock);
    void process(juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi);
    void reset();

    void applyPatch(const SynthPatch& patch);
    const SynthPatch& currentPatch() const { return mPatch; }

    void noteOn (int midiNote, int velocity);
    void noteOff(int midiNote);

    const std::vector<WavetableBank>& getBanks() const { return mBanks; }

    void  setMasterVolume(float v) noexcept { mMasterVolume.store(juce::jlimit(0.f, 1.f, v)); }
    float getLfo1Level()     const noexcept { return mLfo1Level.load(); }
    float getLfo2Level()     const noexcept { return mLfo2Level.load(); }

    static constexpr int kNumVoices = 8;

private:
    std::vector<WavetableBank> mBanks;
    std::array<SynthVoice, kNumVoices> mVoices;

    LfoGenerator mLfo1, mLfo2;
    std::vector<float> mLfo1Buf, mLfo2Buf;

    DriveProcessor mDrive;
    ReverbEffect   mReverb;

    std::atomic<float> mMasterVolume{0.7f};
    std::atomic<float> mLfo1Level{0.f};
    std::atomic<float> mLfo2Level{0.f};

    SynthPatch mPatch;
    double     mSampleRate = 44100.0;
    int        mBlockSize  = 512;

    juce::AudioBuffer<float> mVoiceSumBuffer;

    int findFreeVoice()  const;
    int findVoiceForNote(int midiNote) const;
    int stealVoice();

    void updateEffectParams();

    int mStealIndex = 0;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SynthEngine)
};
