#include "PatchPanel.h"
#include "SynthUtils.h"
#include "UIColors.h"

static const int kTitleH   = 20;
static const int kLabelH   = 16;
static const int kWaveH    = 50;
static const int kPosH     = 22;
static const int kPad      = 6;
static const int kAdsrPrvH = 68;

// Param index reference (38 total):
//  0=osc1_table  1=osc1_pos  2=osc1_octave
//  3=osc2_table  4=osc2_pos  5=osc2_detune  6=osc2_semis
//  7=mix_osc1    8=mix_osc2  9=mix_noise
//  10=lp_cutoff  11=lp_res  12=hp_cutoff  13=hp_res  14=keytrack
//  15-18=amp ADSR   19-24=fenv A/D/S/R/amt/wt
//  25-28=lfo1   29-32=lfo2
//  33-34=drive  35-37=reverb

static const char* kFriendlyNames[SynthPatch::kNumParams] = {
    "Table",  "Pos",    "Oct",
    "Table",  "Pos",    "Detune", "Semis",
    "OSC 1",  "OSC 2",  "Noise",
    "LP Cut", "LP Res", "HP Cut", "HP Res", "Key Follow",
    "A", "D", "S", "R",
    "A", "D", "S", "R", "to Filter", "to WT",
    "Rate", "Shape", "to Pitch", "to Filter",
    "Rate", "Shape", "to WT Pos", "to Amp",
    "Drive", "Tone",
    "Time",  "Damp",  "Mix"
};

// ── Display value formatter ─────────────────────────────────────────────────
juce::String PatchPanel::getDisplayValue(int i, float v) const
{
    auto pct = [](float x) { return juce::String(juce::roundToInt(x * 100.f)) + "%"; };
    auto ms  = [](float sec) -> juce::String {
        if (sec < 1.f) return juce::String(juce::roundToInt(sec * 1000.f)) + "ms";
        return juce::String(sec, 2) + "s";
    };
    auto waveName = [](float x) -> juce::String {
        switch (juce::roundToInt(x * 3.f)) {
            case 0:  return "Sine";
            case 1:  return "Tri";
            case 2:  return "Saw";
            default: return "Sqr";
        }
    };
    auto hzDisplay = [](float v2) -> juce::String {
        const float hz = SynthUtils::logParam(v2, 20.f, 18000.f);
        return hz < 1000.f ? juce::String(juce::roundToInt(hz)) + "Hz"
                           : juce::String(hz / 1000.f, 1) + "kHz";
    };

    switch (i)
    {
        case 0: case 3:
        {
            if (mBanks && !mBanks->empty()) {
                const int N = (int)mBanks->size();
                const int idx = juce::jlimit(0, N-1, juce::roundToInt(v * (float)(N-1)));
                return (*mBanks)[idx].name;
            }
            return juce::String(juce::roundToInt(v * 6.f)) + "/7";
        }
        case 1: case 4:  return pct(v);
        case 2:  { const int oct = static_cast<int>(std::round(v * 4.f)) - 2;
                   return (oct > 0 ? "+" : "") + juce::String(oct) + "oct"; }
        case 5:  { const int ct = juce::roundToInt((v - 0.5f) * 100.f);
                   return (ct >= 0 ? "+" : "") + juce::String(ct) + "ct"; }
        case 6:  { const int s  = juce::roundToInt((v - 0.5f) * 48.f);
                   return (s  >= 0 ? "+" : "") + juce::String(s)  + "st"; }
        case 7: case 8: case 9: return pct(v);
        case 10: case 12: return hzDisplay(v);           // LP / HP cutoff
        case 11: case 13: return "Q " + juce::String(0.5f + v * 9.5f, 1);  // LP / HP res
        case 14: return pct(v);                           // keytrack
        case 15: case 19: return ms(SynthUtils::logParam(v, 0.0005f, 5.f));
        case 16: case 20: return ms(SynthUtils::logParam(v, 0.001f,  5.f));
        case 17: case 21: return pct(v);
        case 18: case 22: return ms(SynthUtils::logParam(v, 0.005f,  10.f));
        case 23: { const int p = juce::roundToInt((v - 0.5f) * 200.f);
                   return (p >= 0 ? "+" : "") + juce::String(p) + "%"; }
        case 24: case 27: case 28: case 31: case 32: return pct(v);
        case 25: case 29: { const float bpm = SynthUtils::logParam(v, 0.01f, 20.f) * 60.f;
                            return bpm < 10.f  ? juce::String(bpm, 2) + " BPM"
                                 : bpm < 100.f ? juce::String(bpm, 1) + " BPM"
                                 :               juce::String(juce::roundToInt(bpm)) + " BPM"; }
        case 26: case 30: return waveName(v);
        default: return pct(v);
    }
}

// ── Constructor ─────────────────────────────────────────────────────────────
PatchPanel::PatchPanel()
{
    buildKnobs();
}

// ── buildKnobs ───────────────────────────────────────────────────────────────
void PatchPanel::buildKnobs()
{
    const SynthPatch defaults;
    const float* defVals = defaults.data();

    for (int i = 0; i < SynthPatch::kNumParams; ++i)
    {
        const float def    = defVals[i];
        // Mixer (7-9) and both ADSR groups (15-22) use vertical faders
        const bool isVert  = (i >= 7 && i <= 9) || (i >= 15 && i <= 22);
        const bool isHoriz = (i == 1 || i == 4);

        auto& sl = mSliders[i];

        if (isVert)
            sl.setSliderStyle(juce::Slider::LinearVertical);
        else if (isHoriz)
            sl.setSliderStyle(juce::Slider::LinearHorizontal);
        else
            sl.setSliderStyle(juce::Slider::Rotary);

        if (sl.getSliderStyle() == juce::Slider::Rotary)
            sl.setRotaryParameters(juce::MathConstants<float>::pi * 1.25f,
                                   juce::MathConstants<float>::pi * 2.75f, true);

        sl.setRange(0.0, 1.0, 0.0);
        sl.setValue(static_cast<double>(def), juce::dontSendNotification);
        sl.setDoubleClickReturnValue(true, static_cast<double>(def));
        sl.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);

        if (i == 2)
            sl.setRange(0.0, 1.0, 0.25);

        if (i == 26 || i == 30)
            sl.setRange(0.0, 1.0, 1.0 / 3.0);

        sl.setWantsKeyboardFocus(false);
        sl.addListener(this);
        addAndMakeVisible(sl);

        auto& vl = mValueLabels[i];
        vl.setText(getDisplayValue(i, def), juce::dontSendNotification);
        vl.setFont(juce::Font(juce::FontOptions("Arial", 12.f, juce::Font::plain)));
        vl.setJustificationType(juce::Justification::centred);
        vl.setColour(juce::Label::textColourId,       juce::Colour(UI::VALUE));
        vl.setColour(juce::Label::backgroundColourId, juce::Colours::transparentBlack);
        vl.setInterceptsMouseClicks(false, false);
        addAndMakeVisible(vl);

        auto& lb = mLabels[i];
        lb.setText(kFriendlyNames[i], juce::dontSendNotification);
        lb.setFont(juce::Font(juce::FontOptions("Arial", 13.f, juce::Font::plain)));
        lb.setJustificationType(juce::Justification::centred);
        lb.setColour(juce::Label::textColourId, juce::Colour(UI::LABEL));
        addAndMakeVisible(lb);
    }

    addAndMakeVisible(mFilterVisualizer);
    addAndMakeVisible(mWaveDisplay1);
    addAndMakeVisible(mWaveDisplay2);
    addAndMakeVisible(mAdsrAmpDisplay);
    addAndMakeVisible(mAdsrFenvDisplay);

    // ── Controls group ────────────────────────────────────────────────────────
    // VEL toggle — empty text; label "Velocity Sens" placed below by layoutControlsGroup
    mVelToggle.setButtonText("");
    mVelToggle.setToggleState(true, juce::dontSendNotification);
    mVelToggle.setWantsKeyboardFocus(false);
    mVelToggle.onClick = [this]() {
        if (onVelocityChanged) onVelocityChanged(mVelToggle.getToggleState());
    };
    addAndMakeVisible(mVelToggle);

    mVelLabel.setText("Velocity Sens", juce::dontSendNotification);
    mVelLabel.setFont(juce::Font(juce::FontOptions("Arial", 13.f, juce::Font::plain)));
    mVelLabel.setJustificationType(juce::Justification::centred);
    mVelLabel.setColour(juce::Label::textColourId, juce::Colour(UI::LABEL));
    addAndMakeVisible(mVelLabel);

    mVolKnob.setSliderStyle(juce::Slider::Rotary);
    mVolKnob.setRotaryParameters(juce::MathConstants<float>::pi * 1.25f,
                                 juce::MathConstants<float>::pi * 2.75f, true);
    mVolKnob.setRange(0.0, 1.0);
    mVolKnob.setValue(0.7);
    mVolKnob.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
    mVolKnob.setDoubleClickReturnValue(true, 0.7);
    mVolKnob.setWantsKeyboardFocus(false);
    mVolKnob.onValueChange = [this]() {
        const float v = static_cast<float>(mVolKnob.getValue());
        mVolValueLabel.setText(juce::String(juce::roundToInt(v * 100.f)) + "%",
                               juce::dontSendNotification);
        if (onVolumeChanged) onVolumeChanged(v);
    };
    addAndMakeVisible(mVolKnob);

    mVolLabel.setText("Volume", juce::dontSendNotification);
    mVolLabel.setFont(juce::Font(juce::FontOptions("Arial", 13.f, juce::Font::plain)));
    mVolLabel.setJustificationType(juce::Justification::centred);
    mVolLabel.setColour(juce::Label::textColourId, juce::Colour(UI::LABEL));
    addAndMakeVisible(mVolLabel);

    mVolValueLabel.setText("70%", juce::dontSendNotification);
    mVolValueLabel.setFont(juce::Font(juce::FontOptions("Arial", 12.f, juce::Font::plain)));
    mVolValueLabel.setJustificationType(juce::Justification::centred);
    mVolValueLabel.setColour(juce::Label::textColourId,       juce::Colour(UI::VALUE));
    mVolValueLabel.setColour(juce::Label::backgroundColourId, juce::Colours::transparentBlack);
    mVolValueLabel.setInterceptsMouseClicks(false, false);
    addAndMakeVisible(mVolValueLabel);

    mAnimToggle.setButtonText("");
    mAnimToggle.setToggleState(true, juce::dontSendNotification);
    mAnimToggle.setWantsKeyboardFocus(false);
    addAndMakeVisible(mAnimToggle);

    mAnimLabel.setText("Show Mod", juce::dontSendNotification);
    mAnimLabel.setFont(juce::Font(juce::FontOptions("Arial", 13.f, juce::Font::plain)));
    mAnimLabel.setJustificationType(juce::Justification::centred);
    mAnimLabel.setColour(juce::Label::textColourId, juce::Colour(UI::LABEL));
    addAndMakeVisible(mAnimLabel);

    startTimerHz(60);
}

// ── Public setters for global controls ───────────────────────────────────────
void PatchPanel::setVelocityEnabled(bool e)
{
    mVelToggle.setToggleState(e, juce::dontSendNotification);
}

void PatchPanel::setMasterVolume(float v)
{
    mVolKnob.setValue(static_cast<double>(v), juce::dontSendNotification);
    mVolValueLabel.setText(juce::String(juce::roundToInt(v * 100.f)) + "%",
                           juce::dontSendNotification);
}

// ── Timer (LFO LEDs + modulation rings + dynamic viz) ────────────────────────
void PatchPanel::timerCallback()
{
    mLfo1Level = onGetLfo1Level ? onGetLfo1Level() : 0.f;
    mLfo2Level = onGetLfo2Level ? onGetLfo2Level() : 0.f;

    if (!mLfoLed1Bounds.isEmpty()) repaint(mLfoLed1Bounds.expanded(2));
    if (!mLfoLed2Bounds.isEmpty()) repaint(mLfoLed2Bounds.expanded(2));

    const bool showMod = mAnimToggle.getToggleState();
    const auto pushMod = [showMod](juce::Slider& sl, double level, double amount, double scale)
    {
        sl.getProperties().set("mod_level",  level);
        sl.getProperties().set("mod_amount", showMod ? amount : 0.0);
        sl.getProperties().set("mod_scale",  scale);
        sl.repaint();
    };

    pushMod(mSliders[10], mLfo1Level, mSliders[28].getValue(), 0.20); // LP cutoff ← LFO1
    pushMod(mSliders[1],  mLfo2Level, mSliders[31].getValue(), 0.50); // OSC1 pos  ← LFO2
    pushMod(mSliders[4],  mLfo2Level, mSliders[31].getValue(), 0.50); // OSC2 pos  ← LFO2

    // Filter ghost — only when animation enabled and LFO1→filter is active
    {
        const float lfoAmt = (float)mSliders[28].getValue();
        if (mAnimToggle.getToggleState() && lfoAmt > 1e-4f)
        {
            float lpHz = SynthUtils::logParam((float)mSliders[10].getValue(), 20.f, 18000.f);
            lpHz *= std::pow(2.f, mLfo1Level * lfoAmt * 2.f);
            lpHz = juce::jlimit(20.f, 18000.f, lpHz);
            const float hpHz = SynthUtils::logParam((float)mSliders[12].getValue(), 20.f, 18000.f);
            mFilterVisualizer.setGhostParams(lpHz, (float)mSliders[11].getValue(),
                                             hpHz, (float)mSliders[13].getValue());
        }
        else { mFilterVisualizer.clearGhost(); }
    }

    // Wave ghost — only when animation enabled and LFO2→WT pos is active
    {
        const float lfo2WtAmt = (float)mSliders[31].getValue();
        if (mAnimToggle.getToggleState() && lfo2WtAmt > 1e-4f && mBanks && !mBanks->empty())
        {
            const int N = (int)mBanks->size();
            for (int osc = 0; osc < 2; ++osc)
            {
                const int tIdx = (osc == 0) ? 0 : 3;
                const int pIdx = (osc == 0) ? 1 : 4;
                const float tNorm = (float)mSliders[tIdx].getValue();
                const float pBase = (float)mSliders[pIdx].getValue();
                const float pLive = juce::jlimit(0.f, 1.f, pBase + mLfo2Level * lfo2WtAmt * 0.5f);
                const int bankIdx = juce::jlimit(0, N - 1,
                                                 juce::roundToInt(tNorm * (float)(N - 1)));
                std::vector<float> frame(WavetableBank::kFrameSize, 0.f);
                (*mBanks)[bankIdx].getInterpolatedFrame(pLive, frame.data());
                WaveDisplay& wd = (osc == 0) ? mWaveDisplay1 : mWaveDisplay2;
                wd.setGhostFrame(frame.data(), WavetableBank::kFrameSize);
            }
        }
        else
        {
            mWaveDisplay1.clearGhost();
            mWaveDisplay2.clearGhost();
        }
    }
}

// ── paint ────────────────────────────────────────────────────────────────────
void PatchPanel::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colour(UI::BG));

    for (const auto& gi : mGroupInfos)
    {
        const auto r = gi.bounds.toFloat();
        g.setColour(juce::Colour(UI::PANEL));
        g.fillRoundedRectangle(r, 7.f);
        g.setColour(juce::Colour(UI::BORDER));
        g.drawRoundedRectangle(r, 7.f, 1.f);

        g.setColour(juce::Colour(UI::TITLE));
        g.setFont(juce::Font(juce::FontOptions("Arial", 13.f, juce::Font::bold)));
        g.drawText(gi.title, gi.bounds.reduced(4, 0).withHeight(kTitleH),
                   juce::Justification::centred, false);
    }

    drawLfoLed(g, mLfoLed1Bounds, mLfo1Level);
    drawLfoLed(g, mLfoLed2Bounds, mLfo2Level);
}

void PatchPanel::drawLfoLed(juce::Graphics& g, juce::Rectangle<int> b, float level)
{
    if (b.isEmpty()) return;
    const float t = (level + 1.f) * 0.5f;
    const juce::Colour col = juce::Colour(UI::LED_DIM).interpolatedWith(juce::Colour(UI::LED_ON), t);
    g.setColour(col);
    g.fillEllipse(b.toFloat().reduced(1.f));
    g.setColour(juce::Colour(UI::LED_ON).darker(0.4f));
    g.drawEllipse(b.toFloat().reduced(1.f), 1.f);
}

// ── placeKnob helper ─────────────────────────────────────────────────────────
void PatchPanel::placeKnob(int idx, int slotX, int innerY, int slotW, int knobSz, int labelH)
{
    const int kx = slotX + (slotW - knobSz) / 2;
    const int ky = innerY;
    mSliders[idx]    .setBounds(kx, ky, knobSz, knobSz);
    mValueLabels[idx].setBounds(kx, ky, knobSz, knobSz);
    mLabels[idx]     .setBounds(slotX, ky + knobSz, slotW, labelH);
}

// ── resized ──────────────────────────────────────────────────────────────────
void PatchPanel::resized()
{
    mGroupInfos.clear();

    auto area  = getLocalBounds().reduced(kPad);
    const int W = area.getWidth();
    const int H = area.getHeight();

    // Row 1 slightly reduced, row 2 significantly taller to give ADSR/Env/LFO room
    const int row1H = H * 36 / 100;
    const int row2H = H * 40 / 100;
    const int row3H = H - row1H - row2H;

    // Row 1 widths — OSC1 == OSC2 (slightly wider, Filter shrinks)
    const int osc1W  = W * 25 / 100;
    const int osc2W  = osc1W;
    const int mixW   = W * 17 / 100;

    // Row 2 widths — fenvW derived after mGlobalKnobSz to guarantee equal preview widths
    const int ampW  = W * 23 / 100;

    // Global knob size — LFO now uses 2x2 grid (2 columns), so lfoSlotW is no longer limiting
    const int osc2KnobAreaH = row1H - kTitleH - kWaveH - kPosH - kLabelH - kPad * 2;
    // LFO has 2 rows of knobs; height per row = half of available knob area (minus inter-row pad)
    const int lfoKnobAreaH  = (row2H - kTitleH - kPad * 3) / 2;
    const int r3KnobAreaH   = row3H - kTitleH - kLabelH - kPad * 2;

    const int osc2SlotW = (osc2W - kPad * 2) / 3;
    const int osc1SlotW = (osc1W - kPad * 2) / 2;

    mGlobalKnobSz = std::min({ osc2SlotW, osc1SlotW,
                               osc2KnobAreaH, lfoKnobAreaH, r3KnobAreaH });
    mGlobalKnobSz = std::max(36, mGlobalKnobSz);

    // fenvW = ampW + extra-knob column width → preview areas are exactly equal
    const int fenvW = ampW + mGlobalKnobSz + kPad * 5;
    const int lfo1W = (W - ampW - fenvW) / 2;

    // Row 3 — three equal blocks
    const int thirdW = W / 3;

    auto row1 = area.removeFromTop(row1H);
    auto row2 = area.removeFromTop(row2H);
    auto row3 = area;

    layoutOscGroup(row1.removeFromLeft(osc1W), "OSC 1", 1, {0, 2},    0);
    layoutOscGroup(row1.removeFromLeft(osc2W), "OSC 2", 4, {3, 5, 6}, 1);
    layoutGroup   (row1.removeFromLeft(mixW),  "Mixer", {7, 8, 9});
    layoutFilterGroup(row1);

    layoutAdsrGroup(row2.removeFromLeft(ampW),  "Amp ADSR",
                    {15,16,17,18}, {}, &mAdsrAmpDisplay);
    layoutAdsrGroup(row2.removeFromLeft(fenvW), "Filter Envelope",
                    {19,20,21,22}, {23,24}, &mAdsrFenvDisplay);
    layoutLfoGroup(row2.removeFromLeft(lfo1W), "LFO 1", {25,26,27,28}, mLfoLed1Bounds);
    layoutLfoGroup(row2,                       "LFO 2", {29,30,31,32}, mLfoLed2Bounds);

    layoutGroup(row3.removeFromLeft(thirdW), "Drive",  {33, 34});
    layoutGroup(row3.removeFromLeft(thirdW), "Reverb", {35, 36, 37});
    layoutControlsGroup(row3);
}

// ── Layout helpers ────────────────────────────────────────────────────────────
void PatchPanel::layoutGroup(juce::Rectangle<int> area, const char* title,
                              std::initializer_list<int> indices)
{
    area.reduce(kPad, kPad);
    mGroupInfos.push_back({ area, title });

    auto inner = area.reduced(kPad, kPad / 2);
    inner.removeFromTop(kTitleH);

    const int n = (int)indices.size();
    if (n == 0) return;

    // If first slider is vertical, use fader layout (same as ADSR but without preview)
    const bool isVert = mSliders[*indices.begin()].getSliderStyle()
                        == juce::Slider::LinearVertical;

    if (isVert)
    {
        const float unitW  = (float)inner.getWidth() / (float)n;
        const int   kValH  = 14;
        const int   sliderH = inner.getHeight() - kLabelH - kValH;
        int xc = inner.getX();
        for (int idx : indices)
        {
            const int sw = juce::roundToInt(unitW);
            mValueLabels[idx].setBounds(xc, inner.getY(),              sw, kValH);
            mSliders[idx]    .setBounds(xc, inner.getY() + kValH,      sw, sliderH);
            mLabels[idx]     .setBounds(xc, inner.getY() + kValH + sliderH, sw, kLabelH);
            xc += sw;
        }
    }
    else
    {
        const int slotW  = inner.getWidth() / n;
        const int innerY = inner.getY() + (inner.getHeight() - mGlobalKnobSz - kLabelH) / 2;
        int col = 0;
        for (int idx : indices)
        {
            placeKnob(idx, inner.getX() + col * slotW, innerY, slotW, mGlobalKnobSz, kLabelH);
            ++col;
        }
    }
}

void PatchPanel::layoutOscGroup(juce::Rectangle<int> area, const char* title,
                                 int posIdx, std::initializer_list<int> knobIndices, int oscIdx)
{
    area.reduce(kPad, kPad);
    mGroupInfos.push_back({ area, title });

    auto inner = area.reduced(kPad, kPad / 2);
    inner.removeFromTop(kTitleH);

    // Wave display
    if (oscIdx == 0) mWaveDisplay1.setBounds(inner.removeFromTop(kWaveH));
    else             mWaveDisplay2.setBounds(inner.removeFromTop(kWaveH));

    // Position fader
    {
        auto posRow = inner.removeFromTop(kPosH).reduced(4, 2);
        mSliders[posIdx]    .setBounds(posRow);
        mValueLabels[posIdx].setBounds(posRow);
        mLabels[posIdx]     .setBounds({});
    }

    inner.removeFromTop(kPad / 2);

    const int n = (int)knobIndices.size();
    if (n == 0) return;

    const int slotW  = inner.getWidth() / n;
    const int innerY = inner.getY() + (inner.getHeight() - mGlobalKnobSz - kLabelH) / 2;
    int col = 0;
    for (int idx : knobIndices)
    {
        placeKnob(idx, inner.getX() + col * slotW, innerY, slotW, mGlobalKnobSz, kLabelH);
        ++col;
    }
}

void PatchPanel::layoutAdsrGroup(juce::Rectangle<int> area, const char* title,
                                  std::initializer_list<int> adsrIndices,
                                  std::initializer_list<int> extraKnobIndices,
                                  AdsrDisplay* preview)
{
    area.reduce(kPad, kPad);
    mGroupInfos.push_back({ area, title });

    auto inner = area.reduced(kPad, kPad / 2);
    inner.removeFromTop(kTitleH);

    const int nAdsr  = (int)adsrIndices.size();
    const int nExtra = (int)extraKnobIndices.size();
    if (nAdsr + nExtra == 0) return;

    // Extra knobs go in a right column (stacked vertically), sliders+preview on the left
    juce::Rectangle<int> leftArea = inner;
    juce::Rectangle<int> rightArea;
    if (nExtra > 0)
    {
        const int rightColW = mGlobalKnobSz + kPad * 4;
        rightArea = leftArea.removeFromRight(rightColW);
        leftArea.removeFromRight(kPad);
    }

    // ADSR preview
    if (preview)
        preview->setBounds(leftArea.removeFromTop(kAdsrPrvH).reduced(2, 2));

    leftArea.removeFromTop(kPad / 2);

    // ADSR sliders: value label above, slider below, name label at bottom
    const float unitW   = (float)leftArea.getWidth() / (float)nAdsr;
    const int   kValH   = 14;
    const int   sliderH = leftArea.getHeight() - kLabelH - kValH;
    int xCursor = leftArea.getX();

    for (int idx : adsrIndices)
    {
        const int sw = juce::roundToInt(unitW);
        mValueLabels[idx].setBounds(xCursor, leftArea.getY(),          sw, kValH);
        mSliders[idx]    .setBounds(xCursor, leftArea.getY() + kValH,  sw, sliderH);
        mLabels[idx]     .setBounds(xCursor, leftArea.getY() + kValH + sliderH, sw, kLabelH);
        xCursor += sw;
    }

    // Extra knobs stacked vertically in right column
    if (nExtra > 0)
    {
        const int knobBlockH = mGlobalKnobSz + kLabelH;
        const int stackH     = nExtra * knobBlockH + (nExtra - 1) * kPad;
        int kyRight = rightArea.getY() + (rightArea.getHeight() - stackH) / 2;
        for (int idx : extraKnobIndices)
        {
            placeKnob(idx, rightArea.getX(), kyRight, rightArea.getWidth(), mGlobalKnobSz, kLabelH);
            kyRight += knobBlockH + kPad;
        }
    }
}

void PatchPanel::layoutLfoGroup(juce::Rectangle<int> area, const char* title,
                                 std::initializer_list<int> indices,
                                 juce::Rectangle<int>& ledOut)
{
    area.reduce(kPad, kPad);
    mGroupInfos.push_back({ area, title });

    auto inner = area.reduced(kPad, kPad / 2);

    auto titleRow = inner.removeFromTop(kTitleH);
    ledOut = titleRow.removeFromRight(14).withSizeKeepingCentre(12, 12);

    const int n = (int)indices.size();   // expected: 4
    if (n == 0) return;

    // 2×2 grid: row 0 = Rate + Shape, row 1 = mod targets
    const int rowH   = mGlobalKnobSz + kLabelH;
    const int totalH = rowH * 2 + kPad;
    int ry = inner.getY() + (inner.getHeight() - totalH) / 2;
    const int slotW  = inner.getWidth() / 2;

    int i = 0;
    for (int idx : indices)
    {
        const int row = i / 2;
        const int col = i % 2;
        placeKnob(idx, inner.getX() + col * slotW, ry + row * (rowH + kPad),
                  slotW, mGlobalKnobSz, kLabelH);
        ++i;
    }
}

void PatchPanel::layoutFilterGroup(juce::Rectangle<int> area)
{
    area.reduce(kPad, kPad);
    mGroupInfos.push_back({ area, "Filter" });

    auto inner = area.reduced(kPad, kPad / 2);
    inner.removeFromTop(kTitleH);

    // 1. Remove bottom knob row first (no kValH row — placeKnob overlays value inside knob)
    const int knobRowH = mGlobalKnobSz + kLabelH;
    auto knobRow = inner.removeFromBottom(knobRowH);

    // 2. Visualizer fills full remaining area (no keytrack column — it moved to Controls)
    mFilterVisualizer.setBounds(inner.reduced(2, 2));

    // Hide keytrack knob (lives in Controls now) from this area
    mSliders[14]    .setBounds({});
    mValueLabels[14].setBounds({});
    mLabels[14]     .setBounds({});

    // 3. Four filter knobs: HP Cut (12), HP Res (13), LP Cut (10), LP Res (11)
    {
        const int order[4] = { 12, 13, 10, 11 };
        const int slotW    = knobRow.getWidth() / 4;
        const int ky       = knobRow.getY();
        for (int i = 0; i < 4; ++i)
            placeKnob(order[i], knobRow.getX() + i * slotW, ky, slotW, mGlobalKnobSz, kLabelH);
    }

    updateFilterVisualizer();
}

void PatchPanel::layoutControlsGroup(juce::Rectangle<int> area)
{
    area.reduce(kPad, kPad);
    mGroupInfos.push_back({ area, "Controls" });

    auto inner = area.reduced(kPad, kPad / 2);
    inner.removeFromTop(kTitleH);

    const int slotW  = inner.getWidth() / 3;
    const int knobKY = inner.getY() + (inner.getHeight() - mGlobalKnobSz - kLabelH) / 2;

    // Slot 1 — both toggles stacked, same 20 px size, evenly distributed
    {
        auto slot1 = inner.removeFromLeft(slotW);
        const int sqSz  = 20;
        const int halfH = slot1.getHeight() / 2;

        // VEL toggle — centred in top half
        {
            const int sqX = slot1.getCentreX() - sqSz / 2;
            const int sqY = slot1.getY() + (halfH - sqSz - kLabelH) / 2;
            mVelToggle.setBounds(sqX, sqY, sqSz, sqSz);
            mVelLabel .setBounds(slot1.getX(), sqY + sqSz, slotW, kLabelH);
        }

        // Anim toggle — centred in bottom half
        {
            const int sqX = slot1.getCentreX() - sqSz / 2;
            const int sqY = slot1.getY() + halfH + (halfH - sqSz - kLabelH) / 2;
            mAnimToggle.setBounds(sqX, sqY, sqSz, sqSz);
            mAnimLabel .setBounds(slot1.getX(), sqY + sqSz, slotW, kLabelH);
        }
    }

    // Slot 2 — Key Follow knob only
    placeKnob(14, inner.getX(), knobKY, slotW, mGlobalKnobSz, kLabelH);
    inner.removeFromLeft(slotW);

    // Slot 3 — Volume knob
    const int kx = inner.getX() + (inner.getWidth() - mGlobalKnobSz) / 2;
    mVolKnob      .setBounds(kx, knobKY, mGlobalKnobSz, mGlobalKnobSz);
    mVolValueLabel.setBounds(kx, knobKY, mGlobalKnobSz, mGlobalKnobSz);
    mVolLabel     .setBounds(inner.getX(), knobKY + mGlobalKnobSz, inner.getWidth(), kLabelH);
}

// ── Wave / ADSR display helpers ───────────────────────────────────────────────
void PatchPanel::updateWaveDisplay(int osc)
{
    WaveDisplay& display = (osc == 0) ? mWaveDisplay1 : mWaveDisplay2;
    if (!mBanks || mBanks->empty()) { display.setFrame(nullptr, 0); return; }

    const int tableIdx = (osc == 0) ? 0 : 3;
    const int posIdx   = (osc == 0) ? 1 : 4;
    const float tNorm  = static_cast<float>(mSliders[tableIdx].getValue());
    const float pNorm  = static_cast<float>(mSliders[posIdx].getValue());

    const int N = (int)mBanks->size();
    const int bankIdx = juce::jlimit(0, N-1, juce::roundToInt(tNorm * (float)(N-1)));

    std::vector<float> frame(WavetableBank::kFrameSize, 0.f);
    (*mBanks)[bankIdx].getInterpolatedFrame(pNorm, frame.data());
    display.setFrame(frame.data(), WavetableBank::kFrameSize);
}

void PatchPanel::updateWaveDisplays()
{
    updateWaveDisplay(0);
    updateWaveDisplay(1);
}

void PatchPanel::updateAdsrDisplays()
{
    // Pass actual times in seconds so the graph uses real proportional widths
    mAdsrAmpDisplay.setValues(
        SynthUtils::logParam((float)mSliders[15].getValue(), 0.0005f, 5.f),
        SynthUtils::logParam((float)mSliders[16].getValue(), 0.001f,  5.f),
        (float)mSliders[17].getValue(),
        SynthUtils::logParam((float)mSliders[18].getValue(), 0.005f,  10.f));

    mAdsrFenvDisplay.setValues(
        SynthUtils::logParam((float)mSliders[19].getValue(), 0.0005f, 5.f),
        SynthUtils::logParam((float)mSliders[20].getValue(), 0.001f,  5.f),
        (float)mSliders[21].getValue(),
        SynthUtils::logParam((float)mSliders[22].getValue(), 0.005f,  10.f));
}

void PatchPanel::updateFilterVisualizer()
{
    const float lpCutHz = SynthUtils::logParam(
        static_cast<float>(mSliders[10].getValue()), 20.f, 18000.f);
    const float lpQ     = static_cast<float>(mSliders[11].getValue());
    const float hpCutHz = SynthUtils::logParam(
        static_cast<float>(mSliders[12].getValue()), 20.f, 18000.f);
    const float hpQ     = static_cast<float>(mSliders[13].getValue());
    mFilterVisualizer.setParams(lpCutHz, lpQ, hpCutHz, hpQ);
}

// ── Public API ────────────────────────────────────────────────────────────────
void PatchPanel::setWavetableBanks(const std::vector<WavetableBank>* banks)
{
    mBanks = banks;
    if (mBanks && !mBanks->empty()) {
        const int N    = (int)mBanks->size();
        const double s = (N > 1) ? 1.0 / (double)(N - 1) : 1.0;
        mSliders[0].setRange(0.0, 1.0, s);
        mSliders[3].setRange(0.0, 1.0, s);
        mValueLabels[0].setText(getDisplayValue(0, (float)mSliders[0].getValue()), juce::dontSendNotification);
        mValueLabels[3].setText(getDisplayValue(3, (float)mSliders[3].getValue()), juce::dontSendNotification);
    }
    updateWaveDisplays();
}

void PatchPanel::setPatch(const SynthPatch& patch)
{
    const float* vals = patch.data();
    for (int i = 0; i < SynthPatch::kNumParams; ++i) {
        mSliders[i].setValue(static_cast<double>(vals[i]), juce::dontSendNotification);
        mValueLabels[i].setText(getDisplayValue(i, vals[i]), juce::dontSendNotification);
    }
    updateWaveDisplays();
    updateAdsrDisplays();
    updateFilterVisualizer();
}

SynthPatch PatchPanel::getPatch() const
{
    SynthPatch p;
    float* vals = p.data();
    for (int i = 0; i < SynthPatch::kNumParams; ++i)
        vals[i] = static_cast<float>(mSliders[i].getValue());
    return p;
}

void PatchPanel::sliderValueChanged(juce::Slider* s)
{
    for (int i = 0; i < SynthPatch::kNumParams; ++i)
    {
        if (&mSliders[i] != s) continue;

        const float val = static_cast<float>(s->getValue());
        mValueLabels[i].setText(getDisplayValue(i, val), juce::dontSendNotification);

        if (i == 0 || i == 1 || i == 3 || i == 4) updateWaveDisplays();
        if (i >= 15 && i <= 22) updateAdsrDisplays();
        if (i >= 10 && i <= 13) updateFilterVisualizer();

        break;
    }

    if (onPatchChanged) onPatchChanged(getPatch());
}

void PatchPanel::setInitPatch(const SynthPatch& patch)
{
    const float* vals = patch.data();
    for (int i = 0; i < SynthPatch::kNumParams; ++i)
        mSliders[i].setDoubleClickReturnValue(true, static_cast<double>(vals[i]));
}
