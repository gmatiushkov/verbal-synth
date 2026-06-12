#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "SynthParameters.h"
#include "WavetableBank.h"
#include "WaveDisplay.h"
#include "AdsrDisplay.h"
#include "FilterVisualizer.h"

class PatchPanel : public juce::Component,
                   private juce::Slider::Listener,
                   private juce::Timer
{
public:
    std::function<void(const SynthPatch&)> onPatchChanged;
    std::function<float()> onGetLfo1Level;
    std::function<float()> onGetLfo2Level;
    std::function<void(bool)>  onVelocityChanged;
    std::function<void(float)> onVolumeChanged;

    PatchPanel();

    void resized() override;
    void paint(juce::Graphics& g) override;

    void setPatch(const SynthPatch& patch);
    SynthPatch getPatch() const;

    void setWavetableBanks(const std::vector<WavetableBank>* banks);
    void setVelocityEnabled(bool e);
    void setMasterVolume(float v);
    void setInitPatch(const SynthPatch& patch);

private:
    std::array<juce::Slider, SynthPatch::kNumParams> mSliders;
    std::array<juce::Label,  SynthPatch::kNumParams> mValueLabels;
    std::array<juce::Label,  SynthPatch::kNumParams> mLabels;

    FilterVisualizer   mFilterVisualizer;

    WaveDisplay  mWaveDisplay1, mWaveDisplay2;
    AdsrDisplay  mAdsrAmpDisplay, mAdsrFenvDisplay;

    // Controls group
    juce::ToggleButton mVelToggle;
    juce::Label        mVelLabel;
    juce::Slider       mVolKnob;
    juce::Label        mVolLabel;
    juce::Label        mVolValueLabel;
    juce::ToggleButton mAnimToggle;
    juce::Label        mAnimLabel;

    const std::vector<WavetableBank>* mBanks = nullptr;

    struct GroupInfo { juce::Rectangle<int> bounds; juce::String title; };
    std::vector<GroupInfo> mGroupInfos;

    juce::Rectangle<int> mLfoLed1Bounds, mLfoLed2Bounds;
    float mLfo1Level = 0.f, mLfo2Level = 0.f;

    int mGlobalKnobSz = 60;

    void buildKnobs();
    void sliderValueChanged(juce::Slider*) override;
    void timerCallback() override;

    // Layout helpers
    void placeKnob(int idx, int slotX, int innerY, int slotW, int knobSz, int labelH);
    void layoutGroup(juce::Rectangle<int>, const char*, std::initializer_list<int>);
    void layoutOscGroup(juce::Rectangle<int>, const char*, int posIdx,
                        std::initializer_list<int> knobIndices, int oscIdx);
    void layoutAdsrGroup(juce::Rectangle<int>, const char*,
                         std::initializer_list<int> adsrIndices,
                         std::initializer_list<int> extraKnobIndices,
                         AdsrDisplay* preview);
    void layoutLfoGroup(juce::Rectangle<int>, const char*,
                        std::initializer_list<int>, juce::Rectangle<int>& ledOut);
    void layoutFilterGroup(juce::Rectangle<int>);
    void layoutControlsGroup(juce::Rectangle<int>);

    void drawLfoLed(juce::Graphics&, juce::Rectangle<int> bounds, float level);

    void updateWaveDisplays();
    void updateWaveDisplay(int osc);
    void updateAdsrDisplays();
    void updateFilterVisualizer();

    juce::String getDisplayValue(int paramIndex, float norm) const;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PatchPanel)
};
