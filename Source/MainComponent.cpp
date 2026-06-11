#include "MainComponent.h"
#include "UIColors.h"

MainComponent::MainComponent()
    : mKeyboard(mKeyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    setSize(1024, 720);
    setLookAndFeel(&mLookAndFeel);

    // ── Title ──
    mTitleLabel.setText("VerbalSynth", juce::dontSendNotification);
    mTitleLabel.setFont(juce::FontOptions(18.f).withStyle("Bold"));
    mTitleLabel.setColour(juce::Label::textColourId, juce::Colour(UI::TITLE));
    mTitleLabel.setJustificationType(juce::Justification::centredLeft);
    addAndMakeVisible(mTitleLabel);

    // ── Preset strip ──
    auto setupBtn = [this](juce::TextButton& btn, const juce::String& text) {
        btn.setButtonText(text);
        btn.setColour(juce::TextButton::buttonColourId,   juce::Colour(UI::BTN_BG));
        btn.setColour(juce::TextButton::textColourOffId,  juce::Colour(UI::BTN_TEXT));
        btn.setColour(juce::TextButton::buttonOnColourId, juce::Colour(UI::KNOB_FILL));
        btn.setWantsKeyboardFocus(false);
        addAndMakeVisible(btn);
    };

    setupBtn(mPrevPresetBtn, "<");
    setupBtn(mNextPresetBtn, ">");
    setupBtn(mPresetNameBtn, mCurrentPresetName);
    setupBtn(mSavePresetBtn, "Save");

    mPrevPresetBtn.onClick = [this]() {
        if (mPresetManager.numPresets() == 0) return;
        const int n = mPresetManager.numPresets();
        const int next = (mCurrentPresetIndex <= 0) ? n - 1 : mCurrentPresetIndex - 1;
        loadPresetByIndex(next);
    };

    mNextPresetBtn.onClick = [this]() {
        if (mPresetManager.numPresets() == 0) return;
        const int n = mPresetManager.numPresets();
        const int next = (mCurrentPresetIndex >= n - 1) ? 0 : mCurrentPresetIndex + 1;
        loadPresetByIndex(next);
    };

    mPresetNameBtn.onClick = [this]() { showPresetDropdown(); };

    mSavePresetBtn.onClick = [this]()
    {
        juce::PopupMenu menu;
        const juce::String overwriteLabel = mCurrentPresetIndex >= 0
            ? "Save \"" + mCurrentPresetName + "\""
            : "Save (no preset selected)";
        menu.addItem(1, overwriteLabel, mCurrentPresetIndex >= 0);
        menu.addItem(2, "Save As New...");
        menu.showMenuAsync(
            juce::PopupMenu::Options().withTargetComponent(&mSavePresetBtn),
            [this](int r) {
                if (r == 1) saveCurrentPreset();
                else if (r == 2) savePresetAs();
            });
    };

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
    mGenerateBtn.setWantsKeyboardFocus(false);
    addAndMakeVisible(mGenerateBtn);

    // ── Velocity toggle ──
    mVelocityToggle.setButtonText("VEL");
    mVelocityToggle.setToggleState(true, juce::dontSendNotification);
    mVelocityToggle.setColour(juce::ToggleButton::textColourId,        juce::Colour(UI::BTN_TEXT));
    mVelocityToggle.setColour(juce::ToggleButton::tickColourId,        juce::Colour(UI::KNOB_FILL));
    mVelocityToggle.setColour(juce::ToggleButton::tickDisabledColourId, juce::Colour(UI::LABEL));
    mVelocityToggle.setWantsKeyboardFocus(false);
    mVelocityToggle.onClick = [this]() {
        mEngine.setVelocityEnabled(mVelocityToggle.getToggleState());
    };
    addAndMakeVisible(mVelocityToggle);

    // ── Volume knob ──
    mVolumeKnob.setSliderStyle(juce::Slider::Rotary);
    mVolumeKnob.setRotaryParameters(juce::MathConstants<float>::pi * 1.2f,
                                    juce::MathConstants<float>::pi * 2.8f, true);
    mVolumeKnob.setRange(0.0, 1.0);
    mVolumeKnob.setValue(0.7);
    mVolumeKnob.setTextBoxStyle(juce::Slider::NoTextBox, false, 0, 0);
    mVolumeKnob.setDoubleClickReturnValue(true, 0.7);
    mVolumeKnob.setWantsKeyboardFocus(false);
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
        if (!mLoadingPreset) markDirty();
    };
    mPatchPanel.onGetLfo1Level = [this]() { return mEngine.getLfo1Level(); };
    mPatchPanel.onGetLfo2Level = [this]() { return mEngine.getLfo2Level(); };
    mPatchPanel.setWavetableBanks(&mEngine.getBanks());
    mPatchPanel.setPatch(mEngine.currentPatch());

    // ── Preset manager ──
    const juce::File patchesDir =
        juce::File::getSpecialLocation(juce::File::currentApplicationFile)
            .getParentDirectory()
            .getChildFile("Patches");
    mPresetManager.setFolder(patchesDir);

    setWantsKeyboardFocus(true);
    addKeyListener(this);
    mKeyboard.setWantsKeyboardFocus(false);

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
    removeKeyListener(this);
    deviceManager.removeMidiInputDeviceCallback({}, &mMidiCollector);
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

    // Left: title + preset strip
    mTitleLabel.setBounds(topBar.removeFromLeft(130));
    topBar.removeFromLeft(4);
    mPrevPresetBtn .setBounds(topBar.removeFromLeft(24).reduced(0, 4));
    mPresetNameBtn .setBounds(topBar.removeFromLeft(150).reduced(0, 4));
    mNextPresetBtn .setBounds(topBar.removeFromLeft(24).reduced(0, 4));
    topBar.removeFromLeft(6);
    mSavePresetBtn .setBounds(topBar.removeFromLeft(64).reduced(0, 4));
    topBar.removeFromLeft(6);

    // Right: VOL label + knob + VEL toggle + gap + Generate
    mVolumeLabel   .setBounds(topBar.removeFromRight(28).reduced(0, 10));
    mVolumeKnob    .setBounds(topBar.removeFromRight(40).reduced(2, 2));
    topBar.removeFromRight(4);
    mVelocityToggle.setBounds(topBar.removeFromRight(52).reduced(0, 4));
    topBar.removeFromRight(8);
    mGenerateBtn   .setBounds(topBar.removeFromRight(100).reduced(0, 4));
    topBar.removeFromRight(6);

    // Middle: prompt
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

// ── Preset management ─────────────────────────────────────────────────────────

void MainComponent::updatePresetLabel()
{
    mPresetNameBtn.setButtonText(mCurrentPresetName + (mPresetDirty ? " *" : ""));
}

void MainComponent::markDirty()
{
    if (!mPresetDirty)
    {
        mPresetDirty = true;
        updatePresetLabel();
    }
}

void MainComponent::loadPresetByIndex(int index)
{
    if (index < 0 || index >= mPresetManager.numPresets()) return;

    mLoadingPreset = true;
    const SynthPatch patch = mPresetManager.loadPreset(index);
    mEngine.applyPatch(patch);
    mPatchPanel.setPatch(patch);
    mLoadingPreset = false;

    mCurrentPresetIndex = index;
    mCurrentPresetName  = mPresetManager.getInfo(index).name;
    mPresetDirty        = false;
    updatePresetLabel();
}

void MainComponent::saveCurrentPreset()
{
    if (mCurrentPresetIndex >= 0)
    {
        mPresetManager.savePreset(mCurrentPresetName, mPatchPanel.getPatch());
        mCurrentPresetIndex = mPresetManager.findByName(mCurrentPresetName);
        mPresetDirty = false;
        updatePresetLabel();
    }
    else
    {
        savePresetAs();
    }
}

void MainComponent::savePresetAs()
{
    auto* aw = new juce::AlertWindow("Save Preset As", "", juce::MessageBoxIconType::NoIcon);
    aw->addTextEditor("name", mCurrentPresetName, "Preset name:");
    aw->addButton("Save",   1, juce::KeyPress(juce::KeyPress::returnKey));
    aw->addButton("Cancel", 0, juce::KeyPress(juce::KeyPress::escapeKey));

    aw->enterModalState(true, juce::ModalCallbackFunction::create(
        [this, aw](int result)
        {
            if (result == 1)
            {
                const juce::String name = aw->getTextEditorContents("name").trim();
                if (name.isNotEmpty())
                {
                    mPresetManager.savePreset(name, mPatchPanel.getPatch());
                    mCurrentPresetIndex = mPresetManager.findByName(name);
                    mCurrentPresetName  = name;
                    mPresetDirty        = false;
                    updatePresetLabel();
                }
            }
            delete aw;
        }), false);
}

void MainComponent::showPresetDropdown()
{
    if (mPresetManager.numPresets() == 0) return;

    juce::PopupMenu menu;
    for (int i = 0; i < mPresetManager.numPresets(); ++i)
        menu.addItem(i + 1, mPresetManager.getInfo(i).name,
                     true, i == mCurrentPresetIndex);

    menu.showMenuAsync(
        juce::PopupMenu::Options().withTargetComponent(&mPresetNameBtn),
        [this](int result) {
            if (result > 0) loadPresetByIndex(result - 1);
        });
}

// ── Computer keyboard → MIDI note map ────────────────────────────────────────
int MainComponent::computerKeyToSemitone(int kc)
{
    const int k = (kc >= 'A' && kc <= 'Z') ? kc + 32 : kc;
    switch (k)
    {
        case 'a': return  0;  case 'w': return  1;
        case 's': return  2;  case 'e': return  3;
        case 'd': return  4;
        case 'f': return  5;  case 't': return  6;
        case 'g': return  7;  case 'y': return  8;
        case 'h': return  9;  case 'u': return 10;
        case 'j': return 11;
        case 'k': return 12;  case 'o': return 13;
        case 'l': return 14;
        default:  return -1;
    }
}

bool MainComponent::keyPressed(const juce::KeyPress& key, juce::Component*)
{
    if (mPromptInput.hasKeyboardFocus(true))
        return false;

    const int kc = key.getKeyCode();
    const int lc = (kc >= 'A' && kc <= 'Z') ? kc + 32 : kc;

    if (key == juce::KeyPress::spaceKey)
    {
        toggleTestNote();
        return true;
    }

    if (lc == 'z') { mKeyboardOctave = juce::jlimit(0, 8, mKeyboardOctave - 1); return true; }
    if (lc == 'x') { mKeyboardOctave = juce::jlimit(0, 8, mKeyboardOctave + 1); return true; }

    const int semitone = computerKeyToSemitone(kc);
    if (semitone < 0) return false;

    if (mActiveComputerKeys.count(lc)) return true;

    const int midiNote = mKeyboardOctave * 12 + semitone;
    if (midiNote < 0 || midiNote > 127) return true;

    mActiveComputerKeys[lc] = midiNote;
    mKeyboardState.noteOn(1, midiNote, 0.8f);
    return true;
}

bool MainComponent::keyStateChanged(bool isKeyDown, juce::Component*)
{
    if (mPromptInput.hasKeyboardFocus(true))
        return false;

    if (isKeyDown)
        return false;

    std::vector<int> released;
    for (auto& [lc, midiNote] : mActiveComputerKeys)
        if (!juce::KeyPress::isKeyCurrentlyDown(lc))
            released.push_back(lc);

    for (int lc : released)
    {
        mKeyboardState.noteOff(1, mActiveComputerKeys[lc], 0.0f);
        mActiveComputerKeys.erase(lc);
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
