#pragma once
#include <unordered_map>
#include <juce_audio_utils/juce_audio_utils.h>
#include "SynthEngine.h"
#include "PatchPanel.h"
#include "VerbalLookAndFeel.h"
#include "PresetManager.h"

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
    bool keyStateChanged(bool isKeyDown, juce::Component*) override;

private:
    VerbalLookAndFeel mLookAndFeel;

    SynthEngine mEngine;
    PatchPanel  mPatchPanel;

    juce::MidiKeyboardState     mKeyboardState;
    juce::MidiKeyboardComponent mKeyboard;
    juce::MidiMessageCollector  mMidiCollector;

    // Top bar — preset strip
    juce::Label      mTitleLabel;
    juce::TextButton mPrevPresetBtn;
    juce::TextButton mPresetNameBtn;
    juce::TextButton mNextPresetBtn;
    juce::TextButton mSavePresetBtn;

    // Top bar — prompt / generate
    juce::TextEditor mPromptInput;
    juce::TextButton mGenerateBtn;

    // Preset manager state
    PresetManager mPresetManager;
    int           mCurrentPresetIndex = -1;
    juce::String  mCurrentPresetName  = "Init";
    bool          mPresetDirty        = false;
    bool          mLoadingPreset      = false;

    // Preset methods
    void loadPresetByIndex(int index);
    void saveCurrentPreset();
    void savePresetAs();
    void showPresetDropdown();
    void updatePresetLabel();
    void markDirty();

    static juce::String initPresetName();
    void ensureInitPreset();
    void loadInitPreset();

    // Computer keyboard MIDI
    bool mNotePlaying = false;
    int  mKeyboardOctave = 4;
    std::unordered_map<int, int> mActiveComputerKeys;

    static int computerKeyToSemitone(int keyCode);

    void toggleTestNote();
    void openAllMidiInputs();

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(MainComponent)
};
