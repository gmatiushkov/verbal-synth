#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "SynthParameters.h"

class PatchPanel : public juce::Component,
                   private juce::Slider::Listener
{
public:
    std::function<void(const SynthPatch&)> onPatchChanged;

    PatchPanel();

    void resized() override;
    void paint(juce::Graphics& g) override;

    void setPatch(const SynthPatch& patch);
    SynthPatch getPatch() const;

private:
    std::array<juce::Slider, SynthPatch::kNumParams> mSliders;
    std::array<juce::Label,  SynthPatch::kNumParams> mValueLabels;
    std::array<juce::Label,  SynthPatch::kNumParams> mLabels;

    struct GroupInfo { juce::Rectangle<int> bounds; juce::String title; };
    std::vector<GroupInfo> mGroupInfos;

    void buildKnobs();
    void sliderValueChanged(juce::Slider*) override;
    void layoutGroup(juce::Rectangle<int>, const char*, std::initializer_list<int>);

    static juce::String getDisplayValue(int paramIndex, float norm);

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PatchPanel)
};
