#include "SynthVoice.h"
#include "SynthUtils.h"
#include <juce_core/juce_core.h>
#include <cmath>

void SynthVoice::prepare(double sampleRate, int blockSize)
{
    mSampleRate = sampleRate;
    mBlockSize  = blockSize;

    mOsc1.prepare(sampleRate);
    mOsc2.prepare(sampleRate);
    mNoise.prepare(sampleRate);
    mLpFilter.prepare(sampleRate, blockSize);
    mHpFilter.prepare(sampleRate, blockSize);
    mAmpEnv.prepare(sampleRate);
    mFilterEnv.prepare(sampleRate);

    mMonoBuf.resize(static_cast<size_t>(blockSize), 0.f);
}

void SynthVoice::setBanks(const std::vector<WavetableBank>* banks)
{
    mBanks = banks;
    updateOscBanks();
}

void SynthVoice::updateOscBanks()
{
    if (mBanks == nullptr || mBanks->empty())
    {
        mOsc1.setBank(nullptr);
        mOsc2.setBank(nullptr);
        return;
    }

    const int size     = static_cast<int>(mBanks->size());
    const int bankIdx1 = juce::jlimit(0, size - 1,
        juce::roundToInt(mPatch.osc1_table * static_cast<float>(size - 1)));
    const int bankIdx2 = juce::jlimit(0, size - 1,
        juce::roundToInt(mPatch.osc2_table * static_cast<float>(size - 1)));

    mOsc1.setBank(&(*mBanks)[bankIdx1]);
    mOsc2.setBank(&(*mBanks)[bankIdx2]);
}

float SynthVoice::computeOsc1Freq() const
{
    const int shift = SynthUtils::octaveShift(mPatch.osc1_octave);
    return SynthUtils::midiToHz(mNote) * std::pow(2.f, static_cast<float>(shift));
}

float SynthVoice::computeOsc2Freq() const
{
    const float baseHz   = computeOsc1Freq();  // OSC2 semis/detune are relative to OSC1 octave
    const int   semis    = static_cast<int>(std::round((mPatch.osc2_semitones - 0.5f) * 48.f));
    const float detCents = (mPatch.osc2_detune - 0.5f) * 100.f;
    return baseHz * std::pow(2.f, static_cast<float>(semis) / 12.f)
                  * SynthUtils::centsToRatio(detCents);
}

void SynthVoice::noteOn(int midiNote, int velocity, const SynthPatch& patch)
{
    mNote    = midiNote;
    mNoteIsOn = true;
    mVelocity = juce::jlimit(0.f, 1.f, static_cast<float>(velocity) / 127.f);

    updatePatch(patch);

    mAmpEnv.reset();
    mFilterEnv.reset();
    mAmpEnv.noteOn();
    mFilterEnv.noteOn();
}

void SynthVoice::noteOff()
{
    mNoteIsOn = false;
    mAmpEnv.noteOff();
    mFilterEnv.noteOff();
}

bool SynthVoice::isActive() const
{
    return mAmpEnv.isActive();
}

void SynthVoice::updatePatch(const SynthPatch& patch)
{
    mPatch = patch;
    updateOscBanks();

    mOsc1.setPosition(patch.osc1_position);
    mOsc2.setPosition(patch.osc2_position);

    mOsc1.setFrequency(computeOsc1Freq(), mSampleRate);
    mOsc2.setFrequency(computeOsc2Freq(), mSampleRate);

    mLpFilter.setTypeAndResonance(0 /*LP*/, patch.lp_resonance);
    mHpFilter.setTypeAndResonance(2 /*HP*/, patch.hp_resonance);

    mAmpEnv.applyParams(patch.amp_attack, patch.amp_decay,
                        patch.amp_sustain, patch.amp_release);
    mFilterEnv.applyParams(patch.fenv_attack, patch.fenv_decay,
                           patch.fenv_sustain, patch.fenv_release);
}

void SynthVoice::renderNextBlock(juce::AudioBuffer<float>& buffer,
                                  int startSample, int numSamples,
                                  const float* lfo1Vals, const float* lfo2Vals)
{
    if (!isActive()) return;
    if (numSamples > static_cast<int>(mMonoBuf.size()))
        mMonoBuf.resize(static_cast<size_t>(numSamples), 0.f);

    const SynthPatch& p = mPatch;

    // Set filter types and resonances once before loop
    mLpFilter.setTypeAndResonance(0, p.lp_resonance);
    mHpFilter.setTypeAndResonance(2, p.hp_resonance);

    // Key tracking base: base frequency of this note
    const float baseHz      = SynthUtils::midiToHz(mNote);
    const float lpBaseCutoff = SynthUtils::logParam(p.lp_cutoff, 20.f, 18000.f);
    const float hpBaseCutoff = SynthUtils::logParam(p.hp_cutoff, 20.f, 18000.f);

    // Filter env amount: 0.5=neutral, range ±4 octaves of LP cutoff shift
    const float fenvAmt = (p.fenv_amount - 0.5f) * 2.f;  // -1..+1

    // Key tracking multiplier (same for both filters)
    float lpKeyCutoff = lpBaseCutoff;
    float hpKeyCutoff = hpBaseCutoff;
    if (p.filter_keytrack > 1e-4f)
    {
        const float keyRatio  = baseHz / 440.f;
        const float keyFactor = std::pow(keyRatio, p.filter_keytrack);
        lpKeyCutoff = lpBaseCutoff + (lpBaseCutoff * keyFactor - lpBaseCutoff) * p.filter_keytrack;
        hpKeyCutoff = hpBaseCutoff + (hpBaseCutoff * keyFactor - hpBaseCutoff) * p.filter_keytrack;
    }

    for (int i = 0; i < numSamples; ++i)
    {
        const float lfo1Val = lfo1Vals != nullptr ? lfo1Vals[i] : 0.f;
        const float lfo2Val = lfo2Vals != nullptr ? lfo2Vals[i] : 0.f;

        // Every 16 samples: update pitch with LFO1 pitch mod
        if ((i & 15) == 0 && p.lfo1_to_pitch > 1e-4f)
        {
            const float semiShift = lfo1Val * p.lfo1_to_pitch * 2.f;  // up to ±2 semitones
            const float pitchMul  = std::pow(2.f, semiShift / 12.f);
            mOsc1.setFrequency(computeOsc1Freq() * pitchMul);
            mOsc2.setFrequency(computeOsc2Freq() * pitchMul);
        }

        // Filter envelope value
        const float fenvVal = mFilterEnv.getNextSample();

        // Wavetable position modulation: base + lfo2 + fenv
        float wt1Pos = p.osc1_position
                     + lfo2Val * p.lfo2_to_wt * 0.5f
                     + fenvVal * p.fenv_to_wt;
        float wt2Pos = p.osc2_position
                     + lfo2Val * p.lfo2_to_wt * 0.5f
                     + fenvVal * p.fenv_to_wt;

        wt1Pos = juce::jlimit(0.f, 1.f, wt1Pos);
        wt2Pos = juce::jlimit(0.f, 1.f, wt2Pos);

        mOsc1.setPosition(wt1Pos);
        mOsc2.setPosition(wt2Pos);

        // LP cutoff: keytrack base + LFO1 + filter env
        float lpCutHz = lpKeyCutoff;

        if (p.lfo1_to_filter > 1e-4f)
            lpCutHz *= std::pow(2.f, lfo1Val * p.lfo1_to_filter * 2.f);  // ±2 oct swing

        if (std::abs(p.fenv_amount - 0.5f) > 1e-4f)
            lpCutHz *= std::pow(2.f, fenvVal * fenvAmt * 4.f);  // ±4 octaves

        lpCutHz = juce::jlimit(20.f, 18000.f, lpCutHz);

        // HP cutoff: keytrack base only (no LFO / env modulation for HP)
        const float hpCutHz = juce::jlimit(20.f, 18000.f, hpKeyCutoff);

        // Oscillators
        const float o1 = mOsc1.getSample() * p.mix_osc1;
        const float o2 = mOsc2.getSample() * p.mix_osc2;
        const float ns = mNoise.getSample() * p.mix_noise;

        const float mixed    = o1 + o2 + ns;
        const float lp_out   = mLpFilter.processSampleRaw(mixed, lpCutHz);
        const float filtered = mHpFilter.processSampleRaw(lp_out, hpCutHz);
        const float envVal   = mAmpEnv.getNextSample();

        // LFO2 tremolo
        const float ampMod = (p.lfo2_to_amp > 1e-4f)
            ? juce::jmax(0.f, 1.f + lfo2Val * p.lfo2_to_amp)
            : 1.f;

        mMonoBuf[i] = filtered * envVal * ampMod * mVelocity;
    }

    mLpFilter.snapToZero();
    mHpFilter.snapToZero();

    // Add mono buffer to both channels
    const int numCh = buffer.getNumChannels();
    for (int ch = 0; ch < numCh; ++ch)
    {
        float* out = buffer.getWritePointer(ch, startSample);
        for (int i = 0; i < numSamples; ++i)
            out[i] += mMonoBuf[i];
    }
}
