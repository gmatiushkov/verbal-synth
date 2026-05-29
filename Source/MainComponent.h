#pragma once
#include <juce_audio_utils/juce_audio_utils.h>
#include "SynthEngine.h"
#include "PatchPanel.h"
#include "VerbalLookAndFeel.h"

class MainComponent : public juce::AudioAppComponent,
                      public juce::KeyListener
{
public:
    MainComponent();
    ~MainComponent() override;

    void prepareToPlay(int samplesPerBlockExpected, double sampleRate) override;
    void getNextAudioBlock(const juce::AudioSourceChannelInfo& info) override;
    void releaseResources() override;

    void paint(juce::Graphics& g) override;
    void resized() override;

    bool keyPressed(const juce::KeyPress& key, juce::Component* source) override;

private:
    VerbalLookAndFeel mLookAndFeel;

    SynthEngine mEngine;
    PatchPanel  mPatchPanel;

    juce::MidiKeyboardState     mKeyboardState;
    juce::MidiKeyboardComponent mKeyboard;
    juce::MidiMessageCollector  mMidiCollector;

    // Top bar
    juce::Label      mTitleLabel;
    juce::TextEditor mPromptInput;
    juce::TextButton mGenerateBtn;
    juce::Slider     mVolumeKnob;
    juce::Label      mVolumeLabel;

    bool mNotePlaying = false;

    void toggleTestNote();
    void openAllMidiInputs();

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(MainComponent)
};
