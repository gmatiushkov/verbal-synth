#include "PatchPanel.h"
#include "SynthUtils.h"

static const char* kFriendlyNames[SynthPatch::kNumParams] = {
    // OSC 1
    "Wave",    "Octave",    "Detune",    "Level",
    // OSC 2
    "Wave",    "Octave",    "Detune",    "Level",
    // Noise / Ring
    "Noise",   "Ring Mod",
    // Filter
    "Type",    "Cutoff",    "Resonance",
    // Amp ADSR
    "Attack",  "Decay",     "Sustain",   "Release",
    // LFO
    "Rate",    "Shape",     "Depth",     "->Filter",  "->Pitch",  "->Amp",
    // Drive
    "Drive",   "Tone",
    // Phaser
    "Rate",    "Depth",     "Feedback",
    // Delay
    "Time",    "Feedback",  "Mix",
    // Reverb
    "Time",    "Damp",      "Mix"
};

juce::String PatchPanel::getDisplayValue(int i, float v)
{
    // 4 waveforms: Sine, Tri, Saw, Square
    auto wave = [](float x) -> juce::String {
        if (x < 0.167f) return "Sine";
        if (x < 0.5f)   return "Tri";
        if (x < 0.833f) return "Saw";
        return "Square";
    };

    auto timeStr = [](float sec) -> juce::String {
        if (sec < 1.f) return juce::String(juce::roundToInt(sec * 1000.f)) + "ms";
        return juce::String(sec, 2) + "s";
    };

    // Param indices (34 total):
    // 0-3: OSC1, 4-7: OSC2, 8-9: Noise/Ring
    // 10-12: Filter, 13-16: ADSR
    // 17: lfo_rate, 18: lfo_shape, 19: lfo_depth, 20: to_filter, 21: to_pitch, 22: to_amp
    // 23: drive_amount, 24: drive_tone, 25-27: phaser, 28-30: delay, 31-33: reverb

    switch (i)
    {
        case 0: case 4:   return wave(v);
        case 1: case 5: {
            int oct = juce::roundToInt(v * 4.f) - 2;
            return (oct >= 0 ? "+" : "") + juce::String(oct) + " oct";
        }
        case 2: case 6: {
            int ct = juce::roundToInt((v - 0.5f) * 100.f);
            return (ct >= 0 ? "+" : "") + juce::String(ct) + " ct";
        }
        case 3: case 7: case 8: case 9:
            return juce::String(juce::roundToInt(v * 100.f)) + "%";
        case 10:
            if (v < 0.25f) return "LPF";
            if (v < 0.75f) return "BPF";
            return "HPF";
        case 11: {
            float hz = SynthUtils::logParam(v, 20.f, 18000.f);
            if (hz < 1000.f) return juce::String(juce::roundToInt(hz)) + " Hz";
            return juce::String(hz / 1000.f, 1) + " kHz";
        }
        case 12:
            return "Q " + juce::String(0.5f + v * 9.5f, 1);
        case 13: return timeStr(SynthUtils::logParam(v, 0.0005f,  5.f));
        case 14: return timeStr(SynthUtils::logParam(v, 0.001f,   5.f));
        case 15: return juce::String(juce::roundToInt(v * 100.f)) + "%";
        case 16: return timeStr(SynthUtils::logParam(v, 0.005f,  10.f));
        case 17: {
            float hz  = SynthUtils::logParam(v, 0.01f, 20.f);
            float bpm = hz * 60.f;
            juce::String hzStr  = (hz < 1.f)
                ? juce::String(hz, 2) + "Hz"
                : juce::String(hz, 1) + "Hz";
            return hzStr + "\n" + juce::String(bpm, 1) + "bpm";
        }
        case 18: return wave(v);  // lfo_shape
        // 19: lfo_depth, 20-22: lfo destinations — all percentages (fall through to default)
        case 25: {  // phaser_rate
            float hz  = 0.01f + v * 7.99f;
            float bpm = hz * 60.f;
            return juce::String(hz, 2) + "Hz\n" + juce::String(bpm, 1) + "bpm";
        }
        case 28: return timeStr(SynthUtils::logParam(v, 0.01f, 1.f));  // delay_time
        default:
            return juce::String(juce::roundToInt(v * 100.f)) + "%";
    }
}

PatchPanel::PatchPanel()
{
    buildKnobs();
}

void PatchPanel::buildKnobs()
{
    const SynthPatch defaults;
    const float* defVals = defaults.data();

    for (int i = 0; i < SynthPatch::kNumParams; ++i)
    {
        const float def = defVals[i];

        auto& sl = mSliders[i];
        sl.setSliderStyle(juce::Slider::Rotary);
        sl.setRotaryParameters(juce::MathConstants<float>::pi * 1.2f,
                               juce::MathConstants<float>::pi * 2.8f, true);
        sl.setRange(0.0, 1.0, 0.0);
        sl.setValue((double)def, juce::dontSendNotification);
        sl.setDoubleClickReturnValue(true, (double)def);
        sl.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
        sl.setColour(juce::Slider::rotarySliderFillColourId,    juce::Colour(0xff5e8fff));
        sl.setColour(juce::Slider::rotarySliderOutlineColourId, juce::Colour(0xff243050));
        sl.setColour(juce::Slider::thumbColourId,               juce::Colour(0xffccd8ff));
        sl.addListener(this);
        addAndMakeVisible(sl);

        auto& vl = mValueLabels[i];
        vl.setText(getDisplayValue(i, def), juce::dontSendNotification);
        vl.setFont(juce::FontOptions(12.f));
        vl.setJustificationType(juce::Justification::centred);
        vl.setColour(juce::Label::textColourId,       juce::Colour(0xffffffff));
        vl.setColour(juce::Label::backgroundColourId, juce::Colours::transparentBlack);
        vl.setInterceptsMouseClicks(false, false);
        addAndMakeVisible(vl);

        auto& lb = mLabels[i];
        lb.setText(kFriendlyNames[i], juce::dontSendNotification);
        lb.setFont(juce::FontOptions(12.f));
        lb.setJustificationType(juce::Justification::centred);
        lb.setColour(juce::Label::textColourId, juce::Colour(0xff7080c0));
        addAndMakeVisible(lb);
    }
}

void PatchPanel::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colour(0xff0f0f22));

    for (const auto& gi : mGroupInfos)
    {
        const auto r = gi.bounds.toFloat();
        g.setColour(juce::Colour(0xff181830));
        g.fillRoundedRectangle(r, 6.f);
        g.setColour(juce::Colour(0xff2a3a5a));
        g.drawRoundedRectangle(r, 6.f, 1.f);

        g.setColour(juce::Colour(0xff7080c0));
        g.setFont(juce::FontOptions(13.f));
        auto titleR = gi.bounds;
        titleR.setHeight(17);
        g.drawText(gi.title, titleR, juce::Justification::centred, false);
    }
}

void PatchPanel::resized()
{
    mGroupInfos.clear();

    auto area = getLocalBounds().reduced(4);
    const int rowH = area.getHeight() / 3;

    auto row1 = area.removeFromTop(rowH);
    layoutGroup(row1.removeFromLeft(row1.getWidth() * 4 / 10), "OSC 1",      {0,1,2,3});
    layoutGroup(row1.removeFromLeft(row1.getWidth() * 4 / 6),  "OSC 2",      {4,5,6,7});
    layoutGroup(row1,                                           "Noise/Ring", {8,9});

    auto row2 = area.removeFromTop(rowH);
    layoutGroup(row2.removeFromLeft(row2.getWidth() * 3 / 10), "Filter",    {10,11,12});
    layoutGroup(row2.removeFromLeft(row2.getWidth() / 2),       "Amp ADSR", {13,14,15,16});
    layoutGroup(row2,                                            "LFO",      {17,18,19,20,21,22});

    auto row3 = area;
    layoutGroup(row3.removeFromLeft(row3.getWidth() * 2 / 10),  "Drive",    {23,24});
    layoutGroup(row3.removeFromLeft(row3.getWidth() * 3 / 8),   "Phaser",   {25,26,27});
    layoutGroup(row3.removeFromLeft(row3.getWidth() / 2),       "Delay",    {28,29,30});
    layoutGroup(row3,                                            "Reverb",   {31,32,33});
}

void PatchPanel::layoutGroup(juce::Rectangle<int> area, const char* title,
                              std::initializer_list<int> indices)
{
    area.reduce(3, 3);
    mGroupInfos.push_back({ area, title });

    const int titleH = 17;
    const int labelH = 14;

    auto inner = area.reduced(3, 2);
    inner.removeFromTop(titleH);

    const int n = (int)indices.size();
    if (n == 0) return;

    const int slotW = inner.getWidth() / n;
    const int knobH = inner.getHeight() - labelH;
    int col = 0;

    for (int idx : indices)
    {
        const int x = inner.getX() + col * slotW;
        const int y = inner.getY();

        mSliders[idx]    .setBounds(x, y,         slotW, knobH);
        mValueLabels[idx].setBounds(x, y,         slotW, knobH);  // overlay on knob
        mLabels[idx]     .setBounds(x, y + knobH, slotW, labelH);

        ++col;
    }
}

void PatchPanel::setPatch(const SynthPatch& patch)
{
    const float* vals = patch.data();
    for (int i = 0; i < SynthPatch::kNumParams; ++i)
    {
        mSliders[i].setValue((double)vals[i], juce::dontSendNotification);
        mValueLabels[i].setText(getDisplayValue(i, vals[i]), juce::dontSendNotification);
    }
}

SynthPatch PatchPanel::getPatch() const
{
    SynthPatch p;
    float* vals = p.data();
    for (int i = 0; i < SynthPatch::kNumParams; ++i)
        vals[i] = (float)mSliders[i].getValue();
    return p;
}

void PatchPanel::sliderValueChanged(juce::Slider* s)
{
    for (int i = 0; i < SynthPatch::kNumParams; ++i)
    {
        if (&mSliders[i] == s)
        {
            mValueLabels[i].setText(getDisplayValue(i, (float)s->getValue()),
                                    juce::dontSendNotification);
            break;
        }
    }
    if (onPatchChanged)
        onPatchChanged(getPatch());
}
