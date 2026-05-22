#include "MainComponent.h"

MainComponent::MainComponent()
    : mKeyboard(mKeyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    setSize(1000, 720);

    addAndMakeVisible(mStatusLabel);
    mStatusLabel.setText("VerbalSynth", juce::dontSendNotification);
    mStatusLabel.setJustificationType(juce::Justification::centredLeft);
    mStatusLabel.setColour(juce::Label::textColourId, juce::Colour(0xff7090d0));

    mKeyboard.setAvailableRange(24, 108);  // C1 to C8
    mKeyboard.setScrollButtonsVisible(false);
    mKeyboard.setColour(juce::MidiKeyboardComponent::keyDownOverlayColourId,
                        juce::Colour(0xff5e8fff));
    mKeyboard.setColour(juce::MidiKeyboardComponent::mouseOverKeyOverlayColourId,
                        juce::Colour(0xff3a5aaf));
    addAndMakeVisible(mKeyboard);

    addAndMakeVisible(mPatchPanel);
    mPatchPanel.setPatch(mEngine.currentPatch());
    mPatchPanel.onPatchChanged = [this](const SynthPatch& p) {
        mEngine.applyPatch(p);
    };

    addKeyListener(this);
    setWantsKeyboardFocus(true);

    mMidiCollector.reset(44100.0);
    setAudioChannels(0, 2);

    // Request small buffer for low latency
    auto setup = deviceManager.getAudioDeviceSetup();
    setup.bufferSize = 128;
    deviceManager.setAudioDeviceSetup(setup, true);

    openAllMidiInputs();
}

MainComponent::~MainComponent()
{
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
    const int numSamples = info.numSamples;
    juce::MidiBuffer midiBuffer;
    mMidiCollector.removeNextBlockOfMessages(midiBuffer, numSamples);
    mKeyboardState.processNextMidiBuffer(midiBuffer, 0, numSamples, true);
    mEngine.process(*info.buffer, midiBuffer);
}

void MainComponent::releaseResources()
{
    mEngine.reset();
}

void MainComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colour(0xff1a1a2e));
}

void MainComponent::resized()
{
    auto area = getLocalBounds();

    auto topBar = area.removeFromTop(36);
    mStatusLabel.setBounds(topBar.reduced(10, 4));

    auto kbArea = area.removeFromBottom(110);
    kbArea.reduce(4, 4);
    mKeyboard.setBounds(kbArea);

    mPatchPanel.setBounds(area.reduced(4, 4));
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
    {
        mKeyboardState.noteOff(1, 60, 0.8f);
        mStatusLabel.setText("VerbalSynth", juce::dontSendNotification);
    }
    else
    {
        mKeyboardState.noteOn(1, 60, 0.8f);
        mStatusLabel.setText("VerbalSynth  [Space] C4 on", juce::dontSendNotification);
    }
    mNotePlaying = !mNotePlaying;
}
