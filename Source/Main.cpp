#include <juce_audio_utils/juce_audio_utils.h>
#include "MainComponent.h"

class VerbalSynthApplication : public juce::JUCEApplication
{
public:
    const juce::String getApplicationName()    override { return "VerbalSynth"; }
    const juce::String getApplicationVersion() override { return "0.1.0"; }
    bool moreThanOneInstanceAllowed()          override { return false; }

    void initialise(const juce::String&) override
    {
        juce::FloatVectorOperations::disableDenormalisedNumberSupport();
        mMainWindow = std::make_unique<MainWindow>(getApplicationName());
    }

    void shutdown() override { mMainWindow.reset(); }

    void systemRequestedQuit() override { quit(); }

private:
    class MainWindow : public juce::DocumentWindow
    {
    public:
        explicit MainWindow(const juce::String& name)
            : DocumentWindow(name,
                             juce::Desktop::getInstance().getDefaultLookAndFeel()
                                 .findColour(juce::ResizableWindow::backgroundColourId),
                             DocumentWindow::allButtons)
        {
            setUsingNativeTitleBar(true);
            setContentOwned(new MainComponent(), true);
            setResizable(true, true);
            centreWithSize(getWidth(), getHeight());
            setVisible(true);
            toFront(true);
            getContentComponent()->grabKeyboardFocus();
        }

        void closeButtonPressed() override
        {
            juce::JUCEApplication::getInstance()->systemRequestedQuit();
        }

    private:
        JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(MainWindow)
    };

    std::unique_ptr<MainWindow> mMainWindow;
};

START_JUCE_APPLICATION(VerbalSynthApplication)
