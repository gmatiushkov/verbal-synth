#pragma once
#include <array>
#include <juce_audio_basics/juce_audio_basics.h>
#include <juce_dsp/juce_dsp.h>
#include "SynthParameters.h"
#include "SynthVoice.h"
#include "LfoGenerator.h"
#include "DriveProcessor.h"
#include "PhaserEffect.h"
#include "DelayEffect.h"
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

    static constexpr int kNumVoices = 8;

private:
    std::array<SynthVoice, kNumVoices> mVoices;

    LfoGenerator   mLfo;
    std::vector<float> mLfoBuf;

    DriveProcessor mDrive;
    PhaserEffect   mPhaser;
    DelayEffect    mDelay;
    ReverbEffect   mReverb;

    SynthPatch mPatch;
    double     mSampleRate  = 44100.0;
    int        mBlockSize   = 512;

    juce::AudioBuffer<float> mVoiceSumBuffer;

    int findFreeVoice()  const;
    int findVoiceForNote(int midiNote) const;
    int stealVoice();

    void updateEffectParams();

    int mStealIndex = 0;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SynthEngine)
};
