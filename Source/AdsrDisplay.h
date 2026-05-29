#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "UIColors.h"

class AdsrDisplay : public juce::Component
{
public:
    void setValues(float a, float d, float s, float r)
    {
        mA = a; mD = d; mS = s; mR = r;
        repaint();
    }

    void paint(juce::Graphics& g) override
    {
        const auto b = getLocalBounds().toFloat().reduced(1.f);

        g.setColour(juce::Colour(UI::ADSR_BG));
        g.fillRoundedRectangle(b, 4.f);
        g.setColour(juce::Colour(UI::BORDER));
        g.drawRoundedRectangle(b, 4.f, 1.f);

        const float pad = 6.f;
        const float x0 = b.getX() + pad;
        const float totalW = b.getWidth() - pad * 2.f;
        const float totalH = b.getHeight() - pad * 2.f;
        const float yBot = b.getY() + b.getHeight() - pad;
        const float yTop = b.getY() + pad;

        const float minSeg = 6.f;
        const float aW = juce::jmax(minSeg, mA  * totalW * 0.30f);
        const float dW = juce::jmax(minSeg, mD  * totalW * 0.25f);
        const float sW = totalW * 0.20f;
        const float rW = juce::jmax(minSeg, mR  * totalW * 0.25f);
        const float scale = totalW / (aW + dW + sW + rW);

        const float aWs = aW * scale;
        const float dWs = dW * scale;
        const float sWs = sW * scale;
        const float rWs = rW * scale;

        const float sustainY = yTop + totalH * (1.f - mS);

        juce::Path env;
        env.startNewSubPath(x0, yBot);
        env.lineTo(x0 + aWs,               yTop);
        env.lineTo(x0 + aWs + dWs,         sustainY);
        env.lineTo(x0 + aWs + dWs + sWs,   sustainY);
        env.lineTo(x0 + aWs + dWs + sWs + rWs, yBot);

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
    float mA = 0.f, mD = 0.3f, mS = 0.8f, mR = 0.3f;
};
