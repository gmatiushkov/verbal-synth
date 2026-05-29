#include "MainComponent.h"
#include "UIColors.h"

MainComponent::MainComponent()
    : mKeyboard(mKeyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    setSize(1280, 820);
    setLookAndFeel(&mLookAndFeel);

    // ── Title ──
    mTitleLabel.setText("VerbalSynth", juce::dontSendNotification);
    mTitleLabel.setFont(juce::FontOptions(18.f).withStyle("Bold"));
    mTitleLabel.setColour(juce::Label::textColourId, juce::Colour(UI::TITLE));
    mTitleLabel.setJustificationType(juce::Justification::centredLeft);
    addAndMakeVisible(mTitleLabel);

    // ── Prompt input ──
    mPromptInput.setMultiLine(false);
    mPromptInput.setReturnKeyStartsNewLine(false);
    mPromptInput.setText("", false);
    mPromptInput.setTextToShowWhenEmpty("Describe a sound... e.g. \"warm pad with long reverb\"",
                                        juce::Colour(UI::LABEL));
    mPromptInput.setFont(juce::FontOptions(14.f));
    addAndMakeVisible(mPromptInput);

    // ── Generate button ──
    mGenerateBtn.setButtonText("Generate");
    mGenerateBtn.setColour(juce::TextButton::buttonColourId,   juce::Colour(UI::BTN_BG));
    mGenerateBtn.setColour(juce::TextButton::textColourOffId,  juce::Colour(UI::BTN_TEXT));
    mGenerateBtn.setColour(juce::TextButton::buttonOnColourId, juce::Colour(UI::KNOB_FILL));
    addAndMakeVisible(mGenerateBtn);

    // ── Volume knob ──
    mVolumeKnob.setSliderStyle(juce::Slider::Rotary);
    mVolumeKnob.setRotaryParameters(juce::MathConstants<float>::pi * 1.2f,
                                    juce::MathConstants<float>::pi * 2.8f, true);
    mVolumeKnob.setRange(0.0, 1.0);
    mVolumeKnob.setValue(0.7);
    mVolumeKnob.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
    mVolumeKnob.setDoubleClickReturnValue(true, 0.7);
    mVolumeKnob.onValueChange = [this]() {
        mEngine.setMasterVolume(static_cast<float>(mVolumeKnob.getValue()));
    };
    mEngine.setMasterVolume(0.7f);
    addAndMakeVisible(mVolumeKnob);

    mVolumeLabel.setText("VOL", juce::dontSendNotification);
    mVolumeLabel.setFont(juce::FontOptions(11.f));
    mVolumeLabel.setColour(juce::Label::textColourId, juce::Colour(UI::LABEL));
    mVolumeLabel.setJustificationType(juce::Justification::centred);
    addAndMakeVisible(mVolumeLabel);

    // ── MIDI keyboard ──
    mKeyboard.setAvailableRange(24, 108);
    mKeyboard.setScrollButtonsVisible(false);
    addAndMakeVisible(mKeyboard);

    // ── Patch panel ──
    addAndMakeVisible(mPatchPanel);
    mPatchPanel.onPatchChanged = [this](const SynthPatch& p) {
        mEngine.applyPatch(p);
    };
    mPatchPanel.onGetLfo1Level = [this]() { return mEngine.getLfo1Level(); };
    mPatchPanel.onGetLfo2Level = [this]() { return mEngine.getLfo2Level(); };
    mPatchPanel.setWavetableBanks(&mEngine.getBanks());
    mPatchPanel.setPatch(mEngine.currentPatch());

    addKeyListener(this);
    setWantsKeyboardFocus(true);

    mMidiCollector.reset(44100.0);
    setAudioChannels(0, 2);

    auto setup = deviceManager.getAudioDeviceSetup();
    setup.bufferSize = 128;
    deviceManager.setAudioDeviceSetup(setup, true);

    openAllMidiInputs();
}

MainComponent::~MainComponent()
{
    setLookAndFeel(nullptr);
    deviceManager.removeMidiInputDeviceCallback({}, &mMidiCollector);
    removeKeyListener(this);
    shutdownAudio();
}

void MainComponent::openAllMidiInputs()
{
    for (const auto& d : juce::MidiInput::getAvailableDevices())
        deviceManager.setMidiInputDeviceEnabled(d.identifier, true);
    deviceManager.addMidiInputDeviceCallback({}, &mMidiCollector);
}

void MainComponent::prepareToPlay(int samplesPerBlockExpected, double sampleRate)
{
    mMidiCollector.reset(sampleRate);
    mEngine.prepare(sampleRate, samplesPerBlockExpected);
}

void MainComponent::getNextAudioBlock(const juce::AudioSourceChannelInfo& info)
{
    juce::MidiBuffer midiBuffer;
    mMidiCollector.removeNextBlockOfMessages(midiBuffer, info.numSamples);
    mKeyboardState.processNextMidiBuffer(midiBuffer, 0, info.numSamples, true);
    mEngine.process(*info.buffer, midiBuffer);
}

void MainComponent::releaseResources()
{
    mEngine.reset();
}

void MainComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colour(UI::BG));

    // Thin separator under top bar
    const int topH = 50;
    g.setColour(juce::Colour(UI::BORDER));
    g.drawLine(0.f, (float)topH, (float)getWidth(), (float)topH, 1.f);
}

void MainComponent::resized()
{
    auto area = getLocalBounds();

    // Top bar
    auto topBar = area.removeFromTop(50);
    topBar.reduce(8, 6);
    mTitleLabel .setBounds(topBar.removeFromLeft(160));
    mVolumeLabel.setBounds(topBar.removeFromRight(28).reduced(0, 10));
    mVolumeKnob .setBounds(topBar.removeFromRight(40).reduced(2, 2));
    topBar.removeFromRight(8);
    mGenerateBtn.setBounds(topBar.removeFromRight(100).reduced(0, 4));
    topBar.removeFromRight(6);
    mPromptInput.setBounds(topBar.reduced(0, 5));

    // Keyboard at bottom — centered
    {
        auto kbRow    = area.removeFromBottom(105);
        auto kbBounds = kbRow.reduced(4, 4);
        const int kbW = juce::jmin(kbBounds.getWidth(), 1100);
        mKeyboard.setBounds(kbBounds.withSizeKeepingCentre(kbW, kbBounds.getHeight()));
    }

    // Patch panel fills rest
    mPatchPanel.setBounds(area.reduced(6, 4));
}

bool MainComponent::keyPressed(const juce::KeyPress& key, juce::Component*)
{
    if (key == juce::KeyPress::spaceKey)
    {
        toggleTestNote();
        return true;
    }
    return false;
}

void MainComponent::toggleTestNote()
{
    if (mNotePlaying)
        mKeyboardState.noteOff(1, 60, 0.8f);
    else
        mKeyboardState.noteOn(1, 60, 0.8f);
    mNotePlaying = !mNotePlaying;
}
