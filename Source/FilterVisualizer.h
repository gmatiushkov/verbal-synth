#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "UIColors.h"
#include <cmath>

// Draws combined LP + HP frequency response curve (series connection).
// Accepts cutoff in Hz and Q value (0..1 normalised → Q 0.5..10).
class FilterVisualizer : public juce::Component
{
public:
    FilterVisualizer()
    {
        setInterceptsMouseClicks(false, false);
    }

    void setParams(float lpCutHz, float lpQ, float hpCutHz, float hpQ)
    {
        mLpCut = lpCutHz;
        mLpQ   = lpQ;
        mHpCut = hpCutHz;
        mHpQ   = hpQ;
        repaint();
    }

    void setGhostParams(float lpCutHz, float lpQ, float hpCutHz, float hpQ)
    {
        mGhostLpCut = lpCutHz; mGhostLpQ = lpQ;
        mGhostHpCut = hpCutHz; mGhostHpQ = hpQ;
        mHasGhost   = true;
        repaint();
    }

    void clearGhost()
    {
        if (mHasGhost) { mHasGhost = false; repaint(); }
    }

    void paint(juce::Graphics& g) override
    {
        const auto b = getLocalBounds().toFloat();

        // Background
        g.setColour(juce::Colour(UI::PANEL).darker(0.15f));
        g.fillRoundedRectangle(b, 4.f);
        g.setColour(juce::Colour(UI::BORDER));
        g.drawRoundedRectangle(b.reduced(0.5f), 4.f, 1.f);

        const int W = getWidth();
        const int H = getHeight();
        if (W < 4 || H < 4) return;

        constexpr float kMinHz   = 20.f;
        constexpr float kMaxHz   = 20000.f;
        constexpr float kMinDb   = -42.f;
        constexpr float kMaxDb   = 24.f;
        constexpr float kDbRange = kMaxDb - kMinDb;

        const float pad = 4.f;
        const float plotW = b.getWidth()  - pad * 2.f;
        const float plotH = b.getHeight() - pad * 2.f;
        const float plotX = b.getX() + pad;
        const float plotY = b.getY() + pad;

        // Grid lines at each decade
        g.setColour(juce::Colour(UI::BORDER));
        for (float gridHz : { 100.f, 1000.f, 10000.f })
        {
            const float xFrac = std::log10(gridHz / kMinHz) / std::log10(kMaxHz / kMinHz);
            const float gx = plotX + xFrac * plotW;
            g.drawLine(gx, plotY, gx, plotY + plotH, 0.5f);
        }

        // 0 dB line
        {
            const float yFrac = (kMaxDb - 0.f) / kDbRange;
            const float gy = plotY + yFrac * plotH;
            g.setColour(juce::Colour(UI::BORDER_HI));
            g.drawLine(plotX, gy, plotX + plotW, gy, 0.5f);
        }

        const int N = juce::jmax(2, (int)plotW);
        const float logMin = std::log10(kMinHz);
        const float logMax = std::log10(kMaxHz);

        // Ghost curve — line only, drawn BEHIND the static curve
        if (mHasGhost)
        {
            juce::Path ghostLine;
            bool gFirst = true;
            for (int xi = 0; xi < N; ++xi)
            {
                const float xFrac = (float)xi / (float)(N - 1);
                const float hz    = std::pow(10.f, logMin + xFrac * (logMax - logMin));
                const float db    = combinedMagDbWith(hz, mGhostLpCut, mGhostLpQ,
                                                          mGhostHpCut, mGhostHpQ);
                const float dbC   = juce::jlimit(kMinDb, kMaxDb, db);
                const float yFrac = (kMaxDb - dbC) / kDbRange;
                const float px    = plotX + xFrac * plotW;
                const float py    = plotY + yFrac * plotH;
                if (gFirst) { ghostLine.startNewSubPath(px, py); gFirst = false; }
                else          ghostLine.lineTo(px, py);
            }
            g.setColour(juce::Colour(UI::ADSR_LINE).withAlpha(0.45f));
            g.strokePath(ghostLine, juce::PathStrokeType(1.5f));
        }

        // Static main curve — always on top
        juce::Path fillPath, linePath;
        bool first = true;
        for (int xi = 0; xi < N; ++xi)
        {
            const float xFrac = (float)xi / (float)(N - 1);
            const float hz    = std::pow(10.f, logMin + xFrac * (logMax - logMin));
            const float db    = combinedMagDb(hz);
            const float dbClamped = juce::jlimit(kMinDb, kMaxDb, db);
            const float yFrac = (kMaxDb - dbClamped) / kDbRange;

            const float px = plotX + xFrac * plotW;
            const float py = plotY + yFrac * plotH;

            if (first)
            {
                fillPath.startNewSubPath(px, plotY + plotH);
                fillPath.lineTo(px, py);
                linePath.startNewSubPath(px, py);
                first = false;
            }
            else
            {
                fillPath.lineTo(px, py);
                linePath.lineTo(px, py);
            }
        }

        fillPath.lineTo(plotX + plotW, plotY + plotH);
        fillPath.closeSubPath();

        g.setColour(juce::Colour(UI::ADSR_FILL));
        g.fillPath(fillPath);

        g.setColour(juce::Colour(UI::ADSR_LINE));
        g.strokePath(linePath, juce::PathStrokeType(1.5f));
    }

private:
    float mLpCut = 18000.f;
    float mLpQ   = 0.5f;
    float mHpCut = 20.f;
    float mHpQ   = 0.5f;

    float mGhostLpCut = 18000.f, mGhostLpQ = 0.5f;
    float mGhostHpCut = 20.f,    mGhostHpQ = 0.5f;
    bool  mHasGhost = false;

    static float magLP(float hz, float cutHz, float q) noexcept
    {
        if (cutHz < 1.f) return 1.f;
        const float r    = hz / cutHz;
        const float r2   = r * r;
        const float denom = std::sqrt((1.f - r2) * (1.f - r2) + (r / q) * (r / q));
        return denom > 0.f ? 1.f / denom : 0.f;
    }

    static float magHP(float hz, float cutHz, float q) noexcept
    {
        if (cutHz < 1.f) return 1.f;
        const float r    = hz / cutHz;
        const float r2   = r * r;
        const float denom = std::sqrt((1.f - r2) * (1.f - r2) + (r / q) * (r / q));
        return denom > 0.f ? r2 / denom : 0.f;
    }

    static float magLP_4th(float hz, float cutHz, float q) noexcept
    {
        return magLP(hz, cutHz, q) * magLP(hz, cutHz, 0.7071f);
    }

    static float magHP_4th(float hz, float cutHz, float q) noexcept
    {
        return magHP(hz, cutHz, q) * magHP(hz, cutHz, 0.7071f);
    }

    float combinedMagDbWith(float hz,
        float lpCut, float lpQ_norm, float hpCut, float hpQ_norm) const noexcept
    {
        const float qLP = 0.5f + lpQ_norm * 9.5f;
        const float qHP = 0.5f + hpQ_norm * 9.5f;
        const float mag = magLP_4th(hz, lpCut, qLP) * magHP_4th(hz, hpCut, qHP);
        return mag > 1e-6f ? 20.f * std::log10(mag) : -120.f;
    }

    float combinedMagDb(float hz) const noexcept
    {
        return combinedMagDbWith(hz, mLpCut, mLpQ, mHpCut, mHpQ);
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(FilterVisualizer)
};
