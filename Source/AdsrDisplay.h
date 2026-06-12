#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "UIColors.h"

// Displays an ADSR envelope shape.
// A, D, R values are actual times in seconds; S is a 0..1 level.
// Segment widths are proportional to real time so the shape correctly reflects the envelope.
class AdsrDisplay : public juce::Component
{
public:
    void setValues(float aSec, float dSec, float s01, float rSec)
    {
        mA = aSec; mD = dSec; mS = s01; mR = rSec;
        repaint();
    }

    void paint(juce::Graphics& g) override
    {
        const auto b = getLocalBounds().toFloat().reduced(1.f);

        g.setColour(juce::Colour(UI::ADSR_BG));
        g.fillRoundedRectangle(b, 4.f);
        g.setColour(juce::Colour(UI::BORDER));
        g.drawRoundedRectangle(b, 4.f, 1.f);

        const float pad    = 6.f;
        const float x0     = b.getX() + pad;
        const float totalW = b.getWidth()  - pad * 2.f;
        const float totalH = b.getHeight() - pad * 2.f;
        const float yBot   = b.getY() + b.getHeight() - pad;
        const float yTop   = b.getY() + pad;

        // Sustain hold gets a fixed 18% of width (it's a level, not a time)
        const float sustW   = totalW * 0.18f;
        const float timeW   = totalW - sustW;

        const float sqA = std::sqrt(mA), sqD = std::sqrt(mD), sqR = std::sqrt(mR);
        const float totalSq = sqA + sqD + sqR;
        float aW, dW, rW;
        if (totalSq > 1e-9f) {
            aW = sqA / totalSq * timeW;
            dW = sqD / totalSq * timeW;
            rW = sqR / totalSq * timeW;
        } else {
            aW = dW = rW = timeW / 3.f;
        }
        const float sW = sustW;

        const float sustainY = yTop + totalH * (1.f - mS);

        juce::Path env;
        env.startNewSubPath(x0, yBot);
        env.lineTo(x0 + aW,              yTop);
        env.lineTo(x0 + aW + dW,         sustainY);
        env.lineTo(x0 + aW + dW + sW,    sustainY);
        env.lineTo(x0 + aW + dW + sW + rW, yBot);

        juce::Path filled = env;
        filled.lineTo(x0, yBot);
        filled.closeSubPath();
        g.setColour(juce::Colour(UI::ADSR_FILL));
        g.fillPath(filled);

        g.setColour(juce::Colour(UI::ADSR_LINE));
        g.strokePath(env, juce::PathStrokeType(1.5f,
            juce::PathStrokeType::curved,
            juce::PathStrokeType::rounded));
    }

private:
    float mA = 0.01f, mD = 0.3f, mS = 0.8f, mR = 0.3f;
};
