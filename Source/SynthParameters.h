#pragma once
#include <array>
#include <string_view>

// 37 synth parameters, normalised to [0.0, 1.0].
struct SynthPatch
{
    // Oscillator 1
    float osc1_table    = 0.0f;   // wavetable bank index
    float osc1_position = 0.0f;   // frame position [0..1]
    float osc1_octave   = 0.5f;   // -2..+2 oct, 5 steps (0,0.25,0.5,0.75,1)

    // Oscillator 2
    float osc2_table     = 0.0f;
    float osc2_position  = 0.0f;
    float osc2_detune    = 0.5f;   // ±50 cents (0.5=no detune)
    float osc2_semitones = 0.5f;   // ±24 semitones (0.5=no shift)

    // Mixer
    float mix_osc1  = 0.8f;
    float mix_osc2  = 0.0f;
    float mix_noise = 0.0f;

    // Filter
    float filter_type      = 0.0f;  // 0=LP, 1=HP (binary toggle)
    float filter_cutoff    = 0.8f;
    float filter_resonance = 0.0f;
    float filter_keytrack  = 0.0f;

    // Amp ADSR
    float amp_attack  = 0.0f;
    float amp_decay   = 0.3f;
    float amp_sustain = 0.8f;
    float amp_release = 0.3f;

    // Filter Env
    float fenv_attack  = 0.0f;
    float fenv_decay   = 0.3f;
    float fenv_sustain = 0.0f;
    float fenv_release = 0.3f;
    float fenv_amount  = 0.5f;   // 0.5=neutral, 0=max neg, 1=max pos
    float fenv_to_wt   = 0.0f;

    // LFO 1
    float lfo1_rate      = 0.3f;
    float lfo1_shape     = 0.0f;
    float lfo1_to_pitch  = 0.0f;
    float lfo1_to_filter = 0.0f;

    // LFO 2
    float lfo2_rate   = 0.2f;
    float lfo2_shape  = 0.0f;
    float lfo2_to_wt  = 0.0f;
    float lfo2_to_amp = 0.0f;

    // Drive
    float drive_amount = 0.0f;
    float drive_tone   = 0.5f;

    // Reverb
    float reverb_time = 0.4f;
    float reverb_damp = 0.5f;
    float reverb_mix  = 0.0f;

    // ---- helpers ----

    static constexpr int kNumParams = 37;

    float*       data()       { return &osc1_table; }
    const float* data() const { return &osc1_table; }

    static constexpr std::array<std::string_view, kNumParams> paramNames()
    {
        return {
            "osc1_table", "osc1_position", "osc1_octave",
            "osc2_table", "osc2_position", "osc2_detune", "osc2_semitones",
            "mix_osc1", "mix_osc2", "mix_noise",
            "filter_type", "filter_cutoff", "filter_resonance", "filter_keytrack",
            "amp_attack", "amp_decay", "amp_sustain", "amp_release",
            "fenv_attack", "fenv_decay", "fenv_sustain", "fenv_release",
            "fenv_amount", "fenv_to_wt",
            "lfo1_rate", "lfo1_shape", "lfo1_to_pitch", "lfo1_to_filter",
            "lfo2_rate", "lfo2_shape", "lfo2_to_wt", "lfo2_to_amp",
            "drive_amount", "drive_tone",
            "reverb_time", "reverb_damp", "reverb_mix"
        };
    }
};

static_assert(sizeof(SynthPatch) == SynthPatch::kNumParams * sizeof(float),
              "SynthPatch layout must be packed floats — 37 floats × 4 = 148 bytes");
