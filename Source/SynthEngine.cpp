#include "SynthEngine.h"

SynthEngine::SynthEngine()
{
    const juce::File wavetableDir =
        juce::File::getSpecialLocation(juce::File::currentApplicationFile)
            .getParentDirectory()
            .getChildFile("Wavetables");

    mBanks = WavetableBank::load(wavetableDir);

    for (auto& v : mVoices)
        v.setBanks(&mBanks);
}

void SynthEngine::prepare(double sampleRate, int samplesPerBlock)
{
    mSampleRate = sampleRate;
    mBlockSize  = samplesPerBlock;

    for (auto& v : mVoices)
        v.prepare(sampleRate, samplesPerBlock);

    mLfo1.prepare(sampleRate);
    mLfo2.prepare(sampleRate);

    const size_t bufSize = static_cast<size_t>(samplesPerBlock);
    mLfo1Buf.resize(bufSize, 0.f);
    mLfo2Buf.resize(bufSize, 0.f);

    mVoiceSumBuffer.setSize(2, samplesPerBlock);

    juce::dsp::ProcessSpec spec{ sampleRate,
                                 static_cast<juce::uint32>(samplesPerBlock), 2 };
    mDrive .prepare(spec);
    mReverb.prepare(spec);

    updateEffectParams();
}

void SynthEngine::process(juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midi)
{
    // --- MIDI ---
    for (const auto meta : midi)
    {
        const auto msg = meta.getMessage();
        if (msg.isNoteOn())
            noteOn(msg.getNoteNumber(), msg.getVelocity());
        else if (msg.isNoteOff())
            noteOff(msg.getNoteNumber());
    }

    const int numSamples = buffer.getNumSamples();

    // --- LFO buffers ---
    if (static_cast<int>(mLfo1Buf.size()) < numSamples)
        mLfo1Buf.resize(static_cast<size_t>(numSamples), 0.f);
    if (static_cast<int>(mLfo2Buf.size()) < numSamples)
        mLfo2Buf.resize(static_cast<size_t>(numSamples), 0.f);

    for (int i = 0; i < numSamples; ++i)
    {
        mLfo1Buf[i] = mLfo1.getNextSample();
        mLfo2Buf[i] = mLfo2.getNextSample();
    }

    // Expose last LFO value for UI LED display (atomic write from audio thread)
    if (numSamples > 0)
    {
        mLfo1Level.store(mLfo1Buf[numSamples - 1]);
        mLfo2Level.store(mLfo2Buf[numSamples - 1]);
    }

    // --- Voices ---
    mVoiceSumBuffer.setSize(2, numSamples, false, false, true);
    mVoiceSumBuffer.clear();

    for (auto& v : mVoices)
        if (v.isActive())
            v.renderNextBlock(mVoiceSumBuffer, 0, numSamples,
                              mLfo1Buf.data(), mLfo2Buf.data());

    for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
        buffer.copyFrom(ch, 0, mVoiceSumBuffer, ch, 0, numSamples);

    buffer.applyGain(1.f / static_cast<float>(kNumVoices));

    // --- Effects ---
    mDrive.setDrive(mPatch.drive_amount);
    mDrive.setTone(mPatch.drive_tone);
    mDrive.processBlock(buffer);

    mReverb.processBlock(buffer);

    // --- Master volume ---
    buffer.applyGain(mMasterVolume.load());
}

void SynthEngine::reset()
{
    for (auto& v : mVoices)
        v.prepare(mSampleRate, mBlockSize);

    mLfo1.reset();
    mLfo2.reset();
    mDrive.reset();
    mReverb.reset();
}

void SynthEngine::applyPatch(const SynthPatch& patch)
{
    mPatch = patch;
    for (auto& v : mVoices)
        if (v.isActive())
            v.updatePatch(patch);
    updateEffectParams();
}

void SynthEngine::noteOn(int midiNote, int velocity)
{
    int idx = findFreeVoice();
    if (idx < 0)
        idx = stealVoice();
    const int vel = mVelocityEnabled ? velocity : 100;
    mVoices[idx].noteOn(midiNote, vel, mPatch);
}

void SynthEngine::noteOff(int midiNote)
{
    for (auto& v : mVoices)
        if (v.isActive() && v.getCurrentNote() == midiNote)
            v.noteOff();
}

int SynthEngine::findFreeVoice() const
{
    for (int i = 0; i < kNumVoices; ++i)
        if (!mVoices[i].isActive())
            return i;
    return -1;
}

int SynthEngine::findVoiceForNote(int midiNote) const
{
    for (int i = 0; i < kNumVoices; ++i)
        if (mVoices[i].isActive() && mVoices[i].getCurrentNote() == midiNote)
            return i;
    return -1;
}

int SynthEngine::stealVoice()
{
    const int idx = mStealIndex % kNumVoices;
    mStealIndex   = (mStealIndex + 1) % kNumVoices;
    return idx;
}

void SynthEngine::updateEffectParams()
{
    mLfo1.setParams(mPatch.lfo1_rate, mPatch.lfo1_shape);
    mLfo2.setParams(mPatch.lfo2_rate, mPatch.lfo2_shape);

    mReverb.setParams(mPatch.reverb_time, mPatch.reverb_damp, mPatch.reverb_mix);
}
