#pragma once
#include <array>
#include <string_view>

// All 34 synth parameters, normalised to [0.0, 1.0].
struct SynthPatch
{
    // Oscillator 1
    float osc1_morph    = 0.5f;   // 0=sine 0.33=tri 0.67=saw 1=square (no RevSaw)
    float osc1_octave   = 0.5f;   // 0=−2oct … 1=+2oct
    float osc1_detune   = 0.5f;   // 0=−50ct, 0.5=0, 1=+50ct
    float osc1_level    = 0.8f;

    // Oscillator 2
    float osc2_morph    = 0.5f;
    float osc2_octave   = 0.5f;
    float osc2_detune   = 0.5f;
    float osc2_level    = 0.0f;

    // Noise + Ring Mod
    float noise_level      = 0.0f;
    float ring_mod_amount  = 0.0f;

    // Filter
    float filter_type      = 0.0f;
    float filter_cutoff    = 0.8f;
    float filter_resonance = 0.0f;

    // Amp ADSR
    float amp_attack   = 0.0f;
    float amp_decay    = 0.3f;
    float amp_sustain  = 0.8f;
    float amp_release  = 0.3f;

    // LFO
    float lfo_rate      = 0.3f;
    float lfo_shape     = 0.0f;
    float lfo_depth     = 0.5f;   // NEW: master LFO depth [0..1]
    float lfo_to_filter = 0.0f;
    float lfo_to_pitch  = 0.0f;
    float lfo_to_amp    = 0.0f;

    // Distortion
    float drive_amount = 0.0f;
    float drive_tone   = 0.5f;

    // Phaser
    float phaser_rate     = 0.2f;
    float phaser_depth    = 0.0f;
    float phaser_feedback = 0.0f;

    // Delay
    float delay_time     = 0.3f;
    float delay_feedback = 0.3f;
    float delay_mix      = 0.0f;

    // Reverb
    float reverb_time     = 0.4f;
    float reverb_damp     = 0.5f;
    float reverb_mix      = 0.0f;

    // ---- helpers ----

    static constexpr int kNumParams = 34;

    float*       data()       { return &osc1_morph; }
    const float* data() const { return &osc1_morph; }

    static constexpr std::array<std::string_view, kNumParams> paramNames()
    {
        return {
            "osc1_morph","osc1_octave","osc1_detune","osc1_level",
            "osc2_morph","osc2_octave","osc2_detune","osc2_level",
            "noise_level","ring_mod_amount",
            "filter_type","filter_cutoff","filter_resonance",
            "amp_attack","amp_decay","amp_sustain","amp_release",
            "lfo_rate","lfo_shape","lfo_depth","lfo_to_filter","lfo_to_pitch","lfo_to_amp",
            "drive_amount","drive_tone",
            "phaser_rate","phaser_depth","phaser_feedback",
            "delay_time","delay_feedback","delay_mix",
            "reverb_time","reverb_damp","reverb_mix"
        };
    }
};
static_assert(sizeof(SynthPatch) == SynthPatch::kNumParams * sizeof(float),
              "SynthPatch layout must be packed floats");
