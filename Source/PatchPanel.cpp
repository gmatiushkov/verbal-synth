#include "PatchPanel.h"
#include "SynthUtils.h"
#include "UIColors.h"

static const int kTitleH   = 20;
static const int kLabelH   = 16;
static const int kWaveH    = 50;
static const int kPosH     = 22;
static const int kPad      = 6;
static const int kAdsrPrvH = 68;

// Param index reference (37 total):
//  0=osc1_table  1=osc1_pos  2=osc1_octave
//  3=osc2_table  4=osc2_pos  5=osc2_detune  6=osc2_semis
//  7=mix_osc1    8=mix_osc2  9=mix_noise
//  10=filter_type 11=cutoff  12=res  13=key
//  14-17=amp ADSR   18-23=fenv A/D/S/R/amt/wt
//  24-27=lfo1   28-31=lfo2
//  32-33=drive  34-36=reverb

static const char* kFriendlyNames[SynthPatch::kNumParams] = {
    "Table",  "Pos",    "Oct",
    "Table",  "Pos",    "Detune", "Semis",
    "OSC 1",  "OSC 2",  "Noise",
    "Type",   "Cutoff", "Res",    "Key",
    "A", "D", "S", "R",
    "A", "D", "S", "R", "Amt", "to WT",
    "Rate", "Shape", "Pitch", "Filter",
    "Rate", "Shape", "WT Pos", "Amp",
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
        case 7: case 8: case 9:   return pct(v);
        case 10: return (v < 0.5f) ? "LP" : "HP";
        case 11: { const float hz = SynthUtils::logParam(v, 20.f, 18000.f);
                   return hz < 1000.f ? juce::String(juce::roundToInt(hz)) + "Hz"
                                      : juce::String(hz / 1000.f, 1) + "kHz"; }
        case 12: return "Q " + juce::String(0.5f + v * 9.5f, 1);
        case 13: return pct(v);
        case 14: case 18: return ms(SynthUtils::logParam(v, 0.0005f, 5.f));
        case 15: case 19: return ms(SynthUtils::logParam(v, 0.001f,  5.f));
        case 16: case 20: return pct(v);
        case 17: case 21: return ms(SynthUtils::logParam(v, 0.005f,  10.f));
        case 22: { const int p = juce::roundToInt((v - 0.5f) * 200.f);
                   return (p >= 0 ? "+" : "") + juce::String(p) + "%"; }
        case 23: case 26: case 27: case 30: case 31: return pct(v);
        case 24: case 28: { const float hz = SynthUtils::logParam(v, 0.01f, 20.f);
                            return hz < 1.f ? juce::String(hz, 2) + "Hz"
                                            : juce::String(hz, 1) + "Hz"; }
        case 25: case 29: return waveName(v);
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
        const bool isVert  = (i >= 14 && i <= 21);
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

        if (i == 25 || i == 29)
            sl.setRange(0.0, 1.0, 1.0 / 3.0);

        sl.setWantsKeyboardFocus(false);
        sl.addListener(this);
        addAndMakeVisible(sl);

        auto& vl = mValueLabels[i];
        vl.setText(getDisplayValue(i, def), juce::dontSendNotification);
        vl.setFont(juce::FontOptions(12.f));
        vl.setJustificationType(juce::Justification::centred);
        vl.setColour(juce::Label::textColourId,       juce::Colour(UI::VALUE));
        vl.setColour(juce::Label::backgroundColourId, juce::Colours::transparentBlack);
        vl.setInterceptsMouseClicks(false, false);
        addAndMakeVisible(vl);

        auto& lb = mLabels[i];
        lb.setText(kFriendlyNames[i], juce::dontSendNotification);
        lb.setFont(juce::FontOptions(13.f));
        lb.setJustificationType(juce::Justification::centred);
        lb.setColour(juce::Label::textColourId, juce::Colour(UI::LABEL));
        addAndMakeVisible(lb);
    }

    mFilterTypeBtn.setWantsKeyboardFocus(false);
    mFilterTypeBtn.setClickingTogglesState(true);
    mFilterTypeBtn.setToggleState(false, juce::dontSendNotification);
    mFilterTypeBtn.setComponentID("filter_toggle");
    mFilterTypeBtn.onClick = [this]() {
        const bool hp = mFilterTypeBtn.getToggleState();
        mSliders[10].setValue(hp ? 1.0 : 0.0, juce::sendNotification);
    };
    addAndMakeVisible(mFilterTypeBtn);

    addAndMakeVisible(mWaveDisplay1);
    addAndMakeVisible(mWaveDisplay2);
    addAndMakeVisible(mAdsrAmpDisplay);
    addAndMakeVisible(mAdsrFenvDisplay);

    startTimerHz(60);
}

// ── Timer (LFO LEDs) ─────────────────────────────────────────────────────────
void PatchPanel::timerCallback()
{
    if (onGetLfo1Level) {
        const float v = onGetLfo1Level();
        if (std::abs(v - mLfo1Level) > 0.01f) {
            mLfo1Level = v;
            if (!mLfoLed1Bounds.isEmpty()) repaint(mLfoLed1Bounds.expanded(2));
        }
    }
    if (onGetLfo2Level) {
        const float v = onGetLfo2Level();
        if (std::abs(v - mLfo2Level) > 0.01f) {
            mLfo2Level = v;
            if (!mLfoLed2Bounds.isEmpty()) repaint(mLfoLed2Bounds.expanded(2));
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
        g.setFont(juce::FontOptions(13.f).withStyle("Bold"));
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

    const int row1H = H * 39 / 100;
    const int row2H = H * 34 / 100;
    const int row3H = H - row1H - row2H;

    // Row 1 widths — OSC1 == OSC2
    const int osc1W  = W * 22 / 100;
    const int osc2W  = osc1W;
    const int mixW   = W * 17 / 100;
    // filtW not needed — filter group gets whatever remains in row1

    // Row 2 widths
    const int ampW   = W * 20 / 100;
    const int fenvW  = W * 27 / 100;
    const int lfo1W  = (W - ampW - fenvW) / 2;
    // lfo2W not needed — LFO2 gets remaining row2 space

    // Row 3 widths
    const int driveW  = W * 28 / 100;
    // reverbW not needed — Reverb gets remaining row3 space

    // Global knob size — most constrained rotary group
    const int osc2KnobAreaH = row1H - kTitleH - kWaveH - kPosH - kLabelH - kPad * 2;
    const int lfoKnobAreaH  = row2H - kTitleH - kLabelH - kPad * 2;
    const int r3KnobAreaH   = row3H - kTitleH - kLabelH - kPad * 2;

    const int mixSlotW  = (mixW  - kPad * 2) / 3;
    const int lfoSlotW  = (lfo1W - kPad * 2) / 4;
    const int osc2SlotW = (osc2W - kPad * 2) / 3;
    const int osc1SlotW = (osc1W - kPad * 2) / 2;

    mGlobalKnobSz = std::min({ mixSlotW, lfoSlotW, osc2SlotW, osc1SlotW,
                               osc2KnobAreaH, lfoKnobAreaH, r3KnobAreaH });
    mGlobalKnobSz = std::max(36, mGlobalKnobSz);

    auto row1 = area.removeFromTop(row1H);
    auto row2 = area.removeFromTop(row2H);
    auto row3 = area;

    layoutOscGroup(row1.removeFromLeft(osc1W), "OSC 1", 1, {0, 2},    0);
    layoutOscGroup(row1.removeFromLeft(osc2W), "OSC 2", 4, {3, 5, 6}, 1);
    layoutGroup   (row1.removeFromLeft(mixW),  "Mixer", {7, 8, 9});
    layoutFilterGroup(row1);

    layoutAdsrGroup(row2.removeFromLeft(ampW),  "Amp ADSR",
                    {14,15,16,17}, {}, &mAdsrAmpDisplay);
    layoutAdsrGroup(row2.removeFromLeft(fenvW), "Filt Env",
                    {18,19,20,21}, {22,23}, &mAdsrFenvDisplay);
    layoutLfoGroup(row2.removeFromLeft(lfo1W), "LFO 1", {24,25,26,27}, mLfoLed1Bounds);
    layoutLfoGroup(row2,                       "LFO 2", {28,29,30,31}, mLfoLed2Bounds);

    layoutGroup(row3.removeFromLeft(driveW),  "Drive",  {32, 33});
    layoutGroup(row3,                         "Reverb", {34, 35, 36});
}

// ── Layout helpers ────────────────────────────────────────────────────────────
void PatchPanel::layoutGroup(juce::Rectangle<int> area, const char* title,
                              std::initializer_list<int> indices)
{
    area.reduce(kPad, kPad);
    mGroupInfos.push_back({ area, title });

    auto inner = area.reduced(kPad, kPad / 2);
    inner.removeFromTop(kTitleH);

    const int n     = (int)indices.size();
    if (n == 0) return;
    const int slotW = inner.getWidth() / n;
    const int innerY = inner.getY() + (inner.getHeight() - mGlobalKnobSz - kLabelH) / 2;

    int col = 0;
    for (int idx : indices)
    {
        placeKnob(idx, inner.getX() + col * slotW, innerY, slotW, mGlobalKnobSz, kLabelH);
        ++col;
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

    const int n = (int)indices.size();
    if (n == 0) return;

    const int slotW  = inner.getWidth() / n;
    const int innerY = inner.getY() + (inner.getHeight() - mGlobalKnobSz - kLabelH) / 2;
    int col = 0;
    for (int idx : indices)
    {
        placeKnob(idx, inner.getX() + col * slotW, innerY, slotW, mGlobalKnobSz, kLabelH);
        ++col;
    }
}

void PatchPanel::layoutFilterGroup(juce::Rectangle<int> area)
{
    area.reduce(kPad, kPad);
    mGroupInfos.push_back({ area, "Filter" });

    auto inner = area.reduced(kPad, kPad / 2);
    inner.removeFromTop(kTitleH);

    // Vertical LP/HP toggle button: width proportional, full inner height
    const int btnW = juce::jmin(56, inner.getWidth() / 5);
    mFilterTypeBtn.setBounds(inner.removeFromLeft(btnW).reduced(2, 4));

    mSliders[10]    .setBounds({});
    mValueLabels[10].setBounds({});
    mLabels[10]     .setBounds({});

    inner.removeFromLeft(kPad);

    // Cutoff(11), Res(12), Key(13)
    const int n     = 3;
    const int slotW = inner.getWidth() / n;
    const int innerY = inner.getY() + (inner.getHeight() - mGlobalKnobSz - kLabelH) / 2;

    for (int i = 0; i < n; ++i)
    {
        const int idx = 11 + i;
        placeKnob(idx, inner.getX() + i * slotW, innerY, slotW, mGlobalKnobSz, kLabelH);
    }
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
    mAdsrAmpDisplay.setValues(
        static_cast<float>(mSliders[14].getValue()),
        static_cast<float>(mSliders[15].getValue()),
        static_cast<float>(mSliders[16].getValue()),
        static_cast<float>(mSliders[17].getValue()));

    mAdsrFenvDisplay.setValues(
        static_cast<float>(mSliders[18].getValue()),
        static_cast<float>(mSliders[19].getValue()),
        static_cast<float>(mSliders[20].getValue()),
        static_cast<float>(mSliders[21].getValue()));
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
    mFilterTypeBtn.setToggleState(patch.filter_type >= 0.5f, juce::dontSendNotification);
    updateWaveDisplays();
    updateAdsrDisplays();
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
        if (i >= 14 && i <= 21) updateAdsrDisplays();
        if (i == 10) mFilterTypeBtn.setToggleState(val >= 0.5f, juce::dontSendNotification);

        break;
    }

    if (onPatchChanged) onPatchChanged(getPatch());
}
