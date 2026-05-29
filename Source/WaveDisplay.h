#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "UIColors.h"
#include <vector>

class WaveDisplay : public juce::Component
{
public:
    void setFrame(const float* samples, int numSamples)
    {
        if (samples != nullptr && numSamples > 0)
            mSamples.assign(samples, samples + numSamples);
        else
            mSamples.clear();
        repaint();
    }

    void paint(juce::Graphics& g) override
    {
        const auto b = getLocalBounds().toFloat();

        g.setColour(juce::Colour(UI::ADSR_BG));
        g.fillRoundedRectangle(b, 4.f);
        g.setColour(juce::Colour(UI::BORDER));
        g.drawRoundedRectangle(b, 4.f, 1.f);

        const float centreY = b.getCentreY();

        if (mSamples.empty())
        {
            g.setColour(juce::Colour(UI::KNOB_FILL).withAlpha(0.5f));
            g.drawLine(b.getX() + 4.f, centreY, b.getRight() - 4.f, centreY, 1.5f);
            return;
        }

        const float drawX = b.getX() + 3.f;
        const float drawW = b.getWidth() - 6.f;
        const float drawH = b.getHeight() - 6.f;
        const float midY  = b.getY() + 3.f + drawH * 0.5f;
        const int   n     = static_cast<int>(mSamples.size());

        juce::Path path;
        for (int i = 0; i < n; ++i)
        {
            const float px = drawX + (float)i / (float)(n - 1) * drawW;
            const float py = midY  - mSamples[i] * (drawH * 0.45f);
            if (i == 0) path.startNewSubPath(px, py);
            else        path.lineTo(px, py);
        }

        g.setColour(juce::Colour(UI::ADSR_LINE));
        g.strokePath(path, juce::PathStrokeType(1.5f));
    }

private:
    std::vector<float> mSamples;
};
