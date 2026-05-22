#include "SynthEngine.h"

SynthEngine::SynthEngine() = default;

void SynthEngine::prepare(double sampleRate, int samplesPerBlock)
{
    mSampleRate = sampleRate;
    mBlockSize  = samplesPerBlock;

    for (auto& v : mVoices)
        v.prepare(sampleRate, samplesPerBlock);

    mLfo.prepare(sampleRate);
    mLfoBuf.resize(static_cast<size_t>(samplesPerBlock), 0.f);
    mVoiceSumBuffer.setSize(2, samplesPerBlock);

    juce::dsp::ProcessSpec spec{ sampleRate,
                                 static_cast<juce::uint32>(samplesPerBlock), 2 };
    mDrive .prepare(spec);
    mPhaser.prepare(spec);
    mDelay .prepare(spec);
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

    // --- Глобальный LFO (единый для всех голосов) ---
    if (static_cast<int>(mLfoBuf.size()) < numSamples)
        mLfoBuf.resize(static_cast<size_t>(numSamples), 0.f);
    for (int i = 0; i < numSamples; ++i)
        mLfoBuf[i] = mLfo.getNextSample();

    // --- Голоса ---
    mVoiceSumBuffer.setSize(2, numSamples, false, false, true);
    mVoiceSumBuffer.clear();

    for (auto& v : mVoices)
        if (v.isActive())
            v.renderNextBlock(mVoiceSumBuffer, 0, numSamples, mLfoBuf.data());

    // Копируем сумму голосов в выходной буфер
    for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
        buffer.copyFrom(ch, 0, mVoiceSumBuffer, ch, 0, numSamples);

    // Нормализация: предотвращает клиппинг при 8 голосах
    buffer.applyGain(1.f / static_cast<float>(kNumVoices));

    // --- Эффекты ---
    mDrive.setDrive(mPatch.drive_amount);
    mDrive.setTone (mPatch.drive_tone);
    mDrive .processBlock(buffer);
    mPhaser.processBlock(buffer);
    mDelay .processBlock(buffer);
    mReverb.processBlock(buffer);
}

void SynthEngine::reset()
{
    for (auto& v : mVoices) v.prepare(mSampleRate, mBlockSize);
    mLfo   .reset();
    mDrive .reset();
    mPhaser.reset();
    mDelay .reset();
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
    mVoices[idx].noteOn(midiNote, velocity, mPatch);
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
    mLfo.setParams(mPatch.lfo_rate, mPatch.lfo_shape);
    mPhaser.setParams(mPatch.phaser_rate, mPatch.phaser_depth, mPatch.phaser_feedback);
    mDelay .setParams(mPatch.delay_time,  mPatch.delay_feedback, mPatch.delay_mix);
    mReverb.setParams(mPatch.reverb_time, mPatch.reverb_damp, mPatch.reverb_mix);
}
