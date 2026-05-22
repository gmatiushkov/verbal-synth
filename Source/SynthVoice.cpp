#include "SynthVoice.h"
#include "SynthUtils.h"
#include <juce_core/juce_core.h>

void SynthVoice::prepare(double sampleRate, int blockSize)
{
    mSampleRate = sampleRate;
    mBlockSize  = blockSize;

    mOsc1 .prepare(sampleRate, blockSize);
    mOsc2 .prepare(sampleRate, blockSize);
    mNoise.prepare(sampleRate);
    mFilter.prepare(sampleRate, blockSize);
    mEnv  .prepare(sampleRate);

    mMonoBuf.resize(static_cast<size_t>(blockSize), 0.f);
}

void SynthVoice::noteOn(int midiNote, int velocity, const SynthPatch& patch)
{
    mNote    = midiNote;
    mPatch   = patch;
    mNoteIsOn = true;

    mOsc1.setMorph(patch.osc1_morph);
    mOsc2.setMorph(patch.osc2_morph);
    mOsc1.setFrequency(computeOscFreq(patch.osc1_octave, patch.osc1_detune), true);
    mOsc2.setFrequency(computeOscFreq(patch.osc2_octave, patch.osc2_detune), true);

    mFilter.setParams(SynthUtils::filterTypeIndex(patch.filter_type),
                      SynthUtils::logParam(patch.filter_cutoff, 20.f, 18000.f),
                      patch.filter_resonance);

    mEnv.applyParams(patch.amp_attack, patch.amp_decay,
                     patch.amp_sustain, patch.amp_release);

    mEnv.reset();
    mEnv.noteOn();

    // Уровень velocity масштабируем линейно [0..1]
    juce::ignoreUnused(velocity);
}

void SynthVoice::noteOff()
{
    mNoteIsOn = false;
    mEnv.noteOff();
}

bool SynthVoice::isActive() const
{
    return mEnv.isActive();
}

void SynthVoice::updatePatch(const SynthPatch& patch)
{
    mPatch = patch;
    mOsc1.setMorph(patch.osc1_morph);
    mOsc2.setMorph(patch.osc2_morph);

    // Apply octave/detune changes to held notes immediately
    mOsc1.setFrequency(computeOscFreq(patch.osc1_octave, patch.osc1_detune));
    mOsc2.setFrequency(computeOscFreq(patch.osc2_octave, patch.osc2_detune));

    mFilter.setParams(SynthUtils::filterTypeIndex(patch.filter_type),
                      SynthUtils::logParam(patch.filter_cutoff, 20.f, 18000.f),
                      patch.filter_resonance);

    mEnv.applyParams(patch.amp_attack, patch.amp_decay,
                     patch.amp_sustain, patch.amp_release);
}

void SynthVoice::renderNextBlock(juce::AudioBuffer<float>& buffer,
                                  int startSample, int numSamples,
                                  const float* lfoValues)
{
    if (!isActive()) return;
    if (numSamples > static_cast<int>(mMonoBuf.size()))
        mMonoBuf.resize(static_cast<size_t>(numSamples), 0.f);

    const SynthPatch& p = mPatch;
    const float baseFreq1 = computeOscFreq(p.osc1_octave, p.osc1_detune);
    const float baseFreq2 = computeOscFreq(p.osc2_octave, p.osc2_detune);

    for (int i = 0; i < numSamples; ++i)
    {
        const float lfoVal = lfoValues[i];  // глобальный LFO из SynthEngine
        const float depth  = p.lfo_depth;

        // LFO → pitch: up to ±1 octave at full depth+to_pitch
        if (p.lfo_to_pitch > 1e-4f && depth > 1e-4f)
        {
            const float semis  = lfoVal * depth * p.lfo_to_pitch;  // [-1, 1]
            const float pitchMul = std::pow(2.f, semis);           // 0.5x..2x
            mOsc1.setFrequency(baseFreq1 * pitchMul);
            mOsc2.setFrequency(baseFreq2 * pitchMul);
        }

        // LFO → filter cutoff: shift-to-fit in normalised space
        if (p.lfo_to_filter > 1e-4f && depth > 1e-4f)
        {
            const float halfSwing = depth * p.lfo_to_filter * 0.5f;
            float lo = p.filter_cutoff - halfSwing;
            float hi = p.filter_cutoff + halfSwing;
            if (lo < 0.f) { hi -= lo; lo = 0.f; }
            if (hi > 1.f) { lo -= (hi - 1.f); hi = 1.f; }
            lo = juce::jmax(0.f, lo);
            hi = juce::jmin(1.f, hi);
            const float normCutoff = lo + (lfoVal + 1.f) * 0.5f * (hi - lo);
            mFilter.setParams(SynthUtils::filterTypeIndex(p.filter_type),
                              SynthUtils::logParam(normCutoff, 20.f, 18000.f),
                              p.filter_resonance);
        }

        const float o1 = mOsc1.renderSample() * p.osc1_level;
        const float o2 = mOsc2.renderSample() * p.osc2_level;
        const float n  = mNoise.getSample()   * p.noise_level;

        const float ring  = o1 * o2;
        const float dry   = o1 + o2;
        const float mixed = dry * (1.f - p.ring_mod_amount)
                          + ring * p.ring_mod_amount
                          + n;

        const float filtered = mFilter.processSample(mixed);
        const float envVal   = mEnv.getNextSample();

        // LFO → amp: 0 (silence) to 2x at full depth+to_amp
        const float ampMod = (depth > 1e-4f && p.lfo_to_amp > 1e-4f)
            ? juce::jmax(0.f, 1.f + lfoVal * depth * p.lfo_to_amp)
            : 1.f;

        mMonoBuf[i] = filtered * envVal * ampMod;
    }

    mFilter.snapToZero();

    // Добавляем моно-буфер к обоим каналам
    const int numCh = buffer.getNumChannels();
    for (int ch = 0; ch < numCh; ++ch)
    {
        float* out = buffer.getWritePointer(ch, startSample);
        for (int i = 0; i < numSamples; ++i)
            out[i] += mMonoBuf[i];
    }
}

float SynthVoice::computeOscFreq(float octaveNorm, float detuneNorm) const
{
    const float baseHz    = SynthUtils::midiToHz(mNote);
    const int   octShift  = SynthUtils::octaveShift(octaveNorm);
    const float detCents  = SynthUtils::detuneInCents(detuneNorm);
    return baseHz * std::pow(2.f, static_cast<float>(octShift)) * SynthUtils::centsToRatio(detCents);
}
