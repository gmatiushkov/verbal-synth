#include "MainComponent.h"
#include "UIColors.h"

// Окно режима разработчика: при закрытии по «X» прячется (не удаляется), а сообщает наружу.
namespace {
class DevLogWindow : public juce::DocumentWindow
{
public:
    explicit DevLogWindow(std::function<void()> onHide)
        : juce::DocumentWindow("VerbalSynth - Developer Log",
                               juce::Colour(0xff141414), juce::DocumentWindow::allButtons),
          mOnHide(std::move(onHide)) {}
    void closeButtonPressed() override { if (mOnHide) mOnHide(); }
private:
    std::function<void()> mOnHide;
};
} // namespace

MainComponent::MainComponent()
    : mKeyboard(mKeyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    setSize(1024, 760);
    setLookAndFeel(&mLookAndFeel);

    // ── Title ──
    mTitleLabel.setText("VerbalSynth", juce::dontSendNotification);
    mTitleLabel.setFont(juce::Font(juce::FontOptions("Arial", 18.f, juce::Font::bold)));
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
    mPromptInput.setFont(juce::Font(juce::FontOptions("Arial", 14.f, juce::Font::plain)));
    addAndMakeVisible(mPromptInput);

    // ── Generate button ──
    mGenerateBtn.setButtonText("Generate");
    mGenerateBtn.setColour(juce::TextButton::buttonColourId,   juce::Colour(UI::BTN_BG));
    mGenerateBtn.setColour(juce::TextButton::textColourOffId,  juce::Colour(UI::BTN_TEXT));
    mGenerateBtn.setColour(juce::TextButton::buttonOnColourId, juce::Colour(UI::KNOB_FILL));
    mGenerateBtn.setWantsKeyboardFocus(false);
    mGenerateBtn.onClick = [this]() { onGenerateClicked(); };
    addAndMakeVisible(mGenerateBtn);

    mPromptInput.onReturnKey = [this]() { onGenerateClicked(); };

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
    mPatchPanel.onVelocityChanged = [this](bool e)  { mEngine.setVelocityEnabled(e); };
    mPatchPanel.onVolumeChanged   = [this](float v) { mEngine.setMasterVolume(v); };
    mPatchPanel.setVelocityEnabled(true);
    mPatchPanel.setMasterVolume(0.7f);
    mEngine.setMasterVolume(0.7f);
    mPatchPanel.setWavetableBanks(&mEngine.getBanks());
    mPatchPanel.setPatch(mEngine.currentPatch());

    // ── Preset manager ──
    const juce::File patchesDir =
        juce::File::getSpecialLocation(juce::File::currentApplicationFile)
            .getParentDirectory()
            .getChildFile("Patches");
    mPresetManager.setFolder(patchesDir);
    ensureInitPreset();
    loadInitPreset();

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

    // Right: Generate button
    mGenerateBtn.setBounds(topBar.removeFromRight(100).reduced(0, 4));
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
        const SynthPatch savedPatch = mPatchPanel.getPatch();
        mPresetManager.savePreset(mCurrentPresetName, savedPatch);
        mCurrentPresetIndex = mPresetManager.findByName(mCurrentPresetName);
        if (mCurrentPresetName.equalsIgnoreCase(initPresetName()))
            mPatchPanel.setInitPatch(savedPatch);
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
                    if (name.equalsIgnoreCase(initPresetName()))
                        mPatchPanel.setInitPatch(mPatchPanel.getPatch());
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

// ── Init preset helpers ───────────────────────────────────────────────────────

juce::String MainComponent::initPresetName()
{
    // "—— Init ——" (two em-dashes each side)
    return juce::String::fromUTF8("\xe2\x80\x94\xe2\x80\x94 Init \xe2\x80\x94\xe2\x80\x94");
}

void MainComponent::ensureInitPreset()
{
    if (mPresetManager.findByName(initPresetName()) < 0)
        mPresetManager.savePreset(initPresetName(), SynthPatch{});
}

void MainComponent::loadInitPreset()
{
    const int idx = mPresetManager.findByName(initPresetName());
    if (idx < 0) return;

    mLoadingPreset = true;
    const SynthPatch patch = mPresetManager.loadPreset(idx);
    mEngine.applyPatch(patch);
    mPatchPanel.setPatch(patch);
    mPatchPanel.setInitPatch(patch);
    mLoadingPreset = false;

    mCurrentPresetIndex = idx;
    mCurrentPresetName  = initPresetName();
    mPresetDirty        = false;
    updatePresetLabel();
}

// ── Generate: текст → патч через ml/scripts/predict.py ───────────────────────
juce::File MainComponent::locatePredictScript() const
{
    // Идём вверх от .exe, пока не найдём ml/scripts/predict.py в дереве проекта.
    juce::File dir = juce::File::getSpecialLocation(juce::File::currentApplicationFile)
                         .getParentDirectory();
    for (int i = 0; i < 8 && dir.exists(); ++i)
    {
        const auto cand = dir.getChildFile("ml").getChildFile("scripts").getChildFile("predict.py");
        if (cand.existsAsFile())
            return cand;
        dir = dir.getParentDirectory();
    }
    return {};
}

bool MainComponent::parsePatchJson(const juce::String& jsonText, SynthPatch& out)
{
    // predict.py печатает в stdout одну строку JSON {param: value}. Вырезаем
    // объект на случай посторонних строк и парсим как PresetManager::loadPreset.
    const juce::String body = jsonText.fromFirstOccurrenceOf("{", true, false)
                                      .upToLastOccurrenceOf("}", true, false);
    const juce::var parsed = juce::JSON::parse(body);
    auto* obj = parsed.getDynamicObject();
    if (obj == nullptr)
        return false;

    // Режим --explain даёт {"params": {...38...}, "explain": {...}} — берём вложенный params.
    if (obj->hasProperty("params"))
        if (auto* inner = obj->getProperty("params").getDynamicObject())
            obj = inner;

    float* data = out.data();
    const auto names = SynthPatch::paramNames();
    int found = 0;
    for (int i = 0; i < SynthPatch::kNumParams; ++i)
    {
        const juce::Identifier key(names[i].data());
        if (obj->hasProperty(key))
        {
            data[i] = juce::jlimit(0.f, 1.f, static_cast<float>(static_cast<double>(obj->getProperty(key))));
            ++found;
        }
    }
    return found == SynthPatch::kNumParams;
}

void MainComponent::onGenerateClicked()
{
    if (mGenerating.exchange(true))   // уже идёт генерация
        return;

    const juce::String prompt = mPromptInput.getText().trim();
    if (prompt.isEmpty())
    {
        mGenerating = false;
        return;
    }

    const juce::File script = locatePredictScript();
    if (! script.existsAsFile())
    {
        mGenerating = false;
        juce::NativeMessageBox::showMessageBoxAsync(
            juce::MessageBoxIconType::WarningIcon, "Generate",
            "Не найден ml/scripts/predict.py рядом с проектом.");
        return;
    }

    mGenerateBtn.setEnabled(false);
    mGenerateBtn.setButtonText("...");

    const bool dev = mDevMode;                       // в dev-режиме просим --explain (разбор для лога)
    juce::Component::SafePointer<MainComponent> safe(this);
    juce::Thread::launch([safe, prompt, script, dev]()
    {
        SynthPatch patch;
        bool ok = false;
        juce::String output;

        juce::ChildProcess proc;
        juce::StringArray args;
        args.add("python");
        args.add(script.getFullPathName());
        if (dev) args.add("--explain");
        args.add(prompt);

        if (proc.start(args, juce::ChildProcess::wantStdOut))
        {
            output = proc.readAllProcessOutput();
            ok = parsePatchJson(output, patch);
            if (! ok)
            {
                DBG("Generate: не удалось распарсить ответ predict.py:\n" << output);
            }
        }
        else
        {
            DBG("Generate: не удалось запустить python predict.py");
        }

        juce::MessageManager::callAsync([safe, patch, ok, dev, output, prompt]()
        {
            if (auto* self = safe.getComponent())
            {
                if (ok)
                {
                    self->mLoadingPreset = true;
                    self->mEngine.applyPatch(patch);
                    self->mPatchPanel.setPatch(patch);
                    self->mLoadingPreset = false;

                    self->mCurrentPresetIndex = -1;          // не привязан к пресету
                    self->mCurrentPresetName  = "Generated";
                    self->markDirty();
                    self->updatePresetLabel();
                }
                if (dev)                                     // лог разбора в окно разработчика
                {
                    // Текст лога формируется в predict.py (поле explain.log) и приходит через JSON —
                    // так кириллица корректна (juce::JSON декодирует UTF-8), без C++-литералов.
                    const juce::String body = output.fromFirstOccurrenceOf("{", true, false)
                                                    .upToLastOccurrenceOf("}", true, false);
                    const juce::var parsed = juce::JSON::parse(body);
                    const juce::var ex = parsed.getProperty(juce::Identifier("explain"), juce::var());
                    const juce::String logText = ex.getProperty(juce::Identifier("log"), juce::var()).toString();
                    if (logText.isNotEmpty())
                        self->appendDevLog(logText + "\n");
                    else
                        self->appendDevLog("QUERY: " + prompt + "  (generation error: no explain)\n\n");
                }
                self->mGenerateBtn.setEnabled(true);
                self->mGenerateBtn.setButtonText("Generate");
                self->mGenerating = false;
            }
        });
    });
}

// ── Режим разработчика: окно-лог разбора генерации (F12) ─────────────────────
void MainComponent::toggleDevMode()
{
    mDevMode = ! mDevMode;
    if (mDevMode)
    {
        if (mDevWindow == nullptr)
        {
            auto* ed = new juce::TextEditor();
            ed->setMultiLine(true);
            ed->setReadOnly(true);                       // только чтение, но текст выделяется и копируется
            ed->setScrollbarsShown(true);
            ed->setCaretVisible(false);
            ed->setFont(juce::Font(juce::FontOptions("Consolas", 13.f, juce::Font::plain)));
            ed->setColour(juce::TextEditor::backgroundColourId, juce::Colour(0xff141414));
            ed->setColour(juce::TextEditor::textColourId,       juce::Colour(0xffd8d8d8));
            mDevLog = ed;

            auto* w = new DevLogWindow([safe = juce::Component::SafePointer<MainComponent>(this)]() {
                if (safe != nullptr) safe->toggleDevMode();   // «X» прячет окно
            });
            w->setContentOwned(ed, false);
            w->setUsingNativeTitleBar(true);
            w->setResizable(true, false);
            w->centreWithSize(580, 640);
            mDevWindow.reset(w);
            // ASCII-интро (кириллицу в C++-литералах MSVC корёжит; русский текст лога приходит из predict.py).
            appendDevLog("VerbalSynth developer log. F12 toggles this window.\n"
                         "After each Generate: query -> retrieval -> modifiers -> param changes.\n"
                         "Text is selectable and copyable.\n\n");
        }
        mDevWindow->setVisible(true);
        mDevWindow->toFront(true);
    }
    else if (mDevWindow != nullptr)
    {
        mDevWindow->setVisible(false);
    }
}

void MainComponent::appendDevLog(const juce::String& text)
{
    if (mDevLog == nullptr) return;
    mDevLog->moveCaretToEnd();
    mDevLog->insertTextAtCaret(text);
    mDevLog->moveCaretToEnd();
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
    if (key == juce::KeyPress::F12Key)        // режим разработчика — работает и при фокусе в поле ввода
    {
        toggleDevMode();
        return true;
    }

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
