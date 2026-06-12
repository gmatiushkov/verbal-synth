#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "UIColors.h"

class VerbalLookAndFeel : public juce::LookAndFeel_V4
{
public:
    VerbalLookAndFeel()
    {
        // TextEditor
        setColour(juce::TextEditor::backgroundColourId,     juce::Colour(UI::INPUT_BG));
        setColour(juce::TextEditor::outlineColourId,        juce::Colour(UI::BORDER));
        setColour(juce::TextEditor::focusedOutlineColourId, juce::Colour(UI::KNOB_FILL));
        setColour(juce::TextEditor::textColourId,           juce::Colour(UI::VALUE));
        setColour(juce::TextEditor::highlightColourId,      juce::Colour(UI::KNOB_FILL).withAlpha(0.4f));
        setColour(juce::TextEditor::highlightedTextColourId,juce::Colour(UI::VALUE));
        setColour(juce::CaretComponent::caretColourId,      juce::Colour(UI::KNOB_THUMB));

        // MidiKeyboard
        setColour(juce::MidiKeyboardComponent::whiteNoteColourId,    juce::Colour(0xffe8eaf0));
        setColour(juce::MidiKeyboardComponent::blackNoteColourId,    juce::Colour(0xff1a2030));
        setColour(juce::MidiKeyboardComponent::keyDownOverlayColourId,   juce::Colour(UI::KNOB_FILL));
        setColour(juce::MidiKeyboardComponent::mouseOverKeyOverlayColourId, juce::Colour(UI::KNOB_FILL).withAlpha(0.5f));
    }

    // ── Rotary knob ────────────────────────────────────────────────────────────
    void drawRotarySlider(juce::Graphics& g, int x, int y, int w, int h,
                          float sliderPos, float startAngle, float endAngle,
                          juce::Slider& slider) override
    {
        const float radius = juce::jmin(w, h) * 0.44f;
        const float cx = x + w * 0.5f;
        const float cy = y + h * 0.5f;
        const float trackThick = juce::jmax(4.f, radius * 0.22f);
        const float arcR = radius - trackThick * 0.5f;

        g.setColour(juce::Colour(UI::KNOB_BG));
        g.fillEllipse(cx - radius, cy - radius, radius * 2.f, radius * 2.f);

        // Track
        {
            juce::Path t;
            t.addCentredArc(cx, cy, arcR, arcR, 0.f, startAngle, endAngle, true);
            g.setColour(juce::Colour(UI::KNOB_TRACK));
            g.strokePath(t, juce::PathStrokeType(trackThick,
                juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
        }

        // Fill
        const float fillAngle = startAngle + sliderPos * (endAngle - startAngle);
        {
            juce::Path f;
            f.addCentredArc(cx, cy, arcR, arcR, 0.f, startAngle, fillAngle, true);
            g.setColour(juce::Colour(UI::KNOB_FILL));
            g.strokePath(f, juce::PathStrokeType(trackThick,
                juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
        }

        const float dotR = trackThick * 0.65f;

        // LFO modulation ring — drawn BEFORE base dot so base dot stays on top
        {
            const float modAmount = (float)(double)slider.getProperties()
                                    .getWithDefault("mod_amount", juce::var(0.0));
            if (modAmount > 1e-4f)
            {
                const float modLevel = (float)(double)slider.getProperties()
                                       .getWithDefault("mod_level", juce::var(0.0));
                const float modScale = (float)(double)slider.getProperties()
                                       .getWithDefault("mod_scale", juce::var(0.25));

                const float arcRange  = endAngle - startAngle;
                const float baseAng   = startAngle + sliderPos * arcRange;
                const float halfDepth = modAmount * modScale * arcRange;

                const float rMin = juce::jlimit(startAngle, endAngle, baseAng - halfDepth);
                const float rMax = juce::jlimit(startAngle, endAngle, baseAng + halfDepth);

                {
                    juce::Path ra;
                    ra.addCentredArc(cx, cy, arcR, arcR, 0.f, rMin, rMax, true);
                    g.setColour(juce::Colour(UI::MOD_COLOR));
                    g.strokePath(ra, juce::PathStrokeType(trackThick,
                        juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
                }

                const float modAng = juce::jlimit(startAngle, endAngle,
                                                  baseAng + modLevel * halfDepth);
                const float mx = cx + std::sin(modAng) * arcR;
                const float my = cy - std::cos(modAng) * arcR;
                g.setColour(juce::Colour(UI::MOD_DOT));
                g.fillEllipse(mx - dotR * 0.8f, my - dotR * 0.8f, dotR * 1.6f, dotR * 1.6f);
            }
        }

        // Base thumb dot — on top of modulation ring
        const float tx = cx + std::sin(fillAngle) * arcR;
        const float ty = cy - std::cos(fillAngle) * arcR;
        g.setColour(juce::Colour(UI::KNOB_THUMB));
        g.fillEllipse(tx - dotR, ty - dotR, dotR * 2.f, dotR * 2.f);
    }

    // ── Linear slider ──────────────────────────────────────────────────────────
    void drawLinearSlider(juce::Graphics& g, int x, int y, int w, int h,
                          float sliderPos, float, float,
                          juce::Slider::SliderStyle style, juce::Slider& slider) override
    {
        if (style == juce::Slider::LinearVertical)
        {
            const float cx     = x + w * 0.5f;
            const float trackW = juce::jmax(3.f, w * 0.08f);
            const float thumbW = juce::jmax(10.f, w * 0.45f);
            const float thumbH = juce::jmax(5.f,  thumbW * 0.26f);

            const float cpV = juce::jlimit((float)y + thumbH * 0.5f,
                                           (float)(y + h) - thumbH * 0.5f, sliderPos);

            g.setColour(juce::Colour(UI::KNOB_TRACK));
            g.fillRoundedRectangle(cx - trackW * 0.5f, (float)y, trackW, (float)h, trackW * 0.5f);

            g.setColour(juce::Colour(UI::KNOB_FILL));
            g.fillRoundedRectangle(cx - trackW * 0.5f, cpV, trackW,
                                   (float)(y + h) - cpV, trackW * 0.5f);

            g.setColour(juce::Colour(UI::KNOB_THUMB));
            g.fillRoundedRectangle(cx - thumbW * 0.5f, cpV - thumbH * 0.5f,
                                   thumbW, thumbH, thumbH * 0.5f);
        }
        else if (style == juce::Slider::LinearHorizontal)
        {
            const float cy     = y + h * 0.5f;
            const float trackH = juce::jmax(4.f, h * 0.18f);
            const float thumbH = juce::jmax(16.f, h * 0.65f);
            const float thumbW = juce::jmax(8.f,  thumbH * 0.38f);

            const float cpH = juce::jlimit((float)x + thumbW * 0.5f,
                                           (float)(x + w) - thumbW * 0.5f, sliderPos);

            g.setColour(juce::Colour(UI::KNOB_TRACK));
            g.fillRoundedRectangle((float)x, cy - trackH * 0.5f, (float)w, trackH, trackH * 0.5f);

            g.setColour(juce::Colour(UI::KNOB_FILL));
            g.fillRoundedRectangle((float)x, cy - trackH * 0.5f,
                                   cpH - (float)x, trackH, trackH * 0.5f);

            // Mod range + ghost thumb (behind base thumb)
            const float modAmount = (float)(double)slider.getProperties()
                                    .getWithDefault("mod_amount", juce::var(0.0));
            if (modAmount > 1e-4f)
            {
                const float modLevel = (float)(double)slider.getProperties()
                                       .getWithDefault("mod_level", juce::var(0.0));
                const float modScale = (float)(double)slider.getProperties()
                                       .getWithDefault("mod_scale", juce::var(0.5));
                const float halfW   = modAmount * modScale * (float)w;
                const float rangeL  = juce::jlimit((float)x, (float)(x + w), cpH - halfW);
                const float rangeR  = juce::jlimit((float)x, (float)(x + w), cpH + halfW);

                g.setColour(juce::Colour(UI::MOD_COLOR));
                g.fillRoundedRectangle(rangeL, cy - trackH * 0.5f,
                                       rangeR - rangeL, trackH, trackH * 0.5f);

                const float liveX = juce::jlimit((float)x + thumbW * 0.5f,
                                                 (float)(x + w) - thumbW * 0.5f,
                                                 cpH + modLevel * halfW);
                g.setColour(juce::Colour(UI::MOD_DOT));
                g.fillRoundedRectangle(liveX - thumbW * 0.5f, cy - thumbH * 0.5f,
                                       thumbW, thumbH, thumbW * 0.5f);
            }

            // Base thumb — on top of mod indicator
            g.setColour(juce::Colour(UI::KNOB_THUMB));
            g.fillRoundedRectangle(cpH - thumbW * 0.5f, cy - thumbH * 0.5f,
                                   thumbW, thumbH, thumbW * 0.5f);
        }
    }

    int getSliderThumbRadius(juce::Slider&) override { return 0; }

    // ── Toggle button — centred checkbox square, no built-in text ─────────────
    void drawToggleButton(juce::Graphics& g, juce::ToggleButton& btn,
                          bool /*highlighted*/, bool /*down*/) override
    {
        const float w  = (float)btn.getWidth();
        const float h  = (float)btn.getHeight();
        const float sz = juce::jmin(w, h);
        const float bx = (w - sz) * 0.5f;
        const float by = (h - sz) * 0.5f;

        g.setColour(juce::Colour(UI::PANEL).brighter(0.12f));
        g.fillRoundedRectangle(bx, by, sz, sz, 3.f);
        g.setColour(juce::Colour(UI::BORDER_HI));
        g.drawRoundedRectangle(bx + 0.5f, by + 0.5f, sz - 1.f, sz - 1.f, 3.f, 1.f);

        if (btn.getToggleState())
        {
            const float inner = sz * 0.58f;
            g.setColour(juce::Colour(UI::KNOB_FILL));
            g.fillRoundedRectangle(bx + (sz - inner) * 0.5f,
                                   by + (sz - inner) * 0.5f,
                                   inner, inner, 2.f);
        }
    }

    // ── Button background — filter toggle vs. normal button ───────────────────
    void drawButtonBackground(juce::Graphics& g, juce::Button& btn,
                              const juce::Colour&, bool isHover, bool isDown) override
    {
        const auto b = btn.getLocalBounds().toFloat().reduced(1.f);

        if (btn.getComponentID() == "filter_toggle")
        {
            const bool isHP = btn.getToggleState();

            g.setColour(juce::Colour(UI::TOGGLE_BG));
            g.fillRoundedRectangle(b, 6.f);
            g.setColour(isDown ? juce::Colour(UI::BORDER_HI) : juce::Colour(UI::BORDER));
            g.drawRoundedRectangle(b, 6.f, 1.5f);

            const float half  = b.getHeight() * 0.5f;
            const float pillH = half - 5.f;
            const float pillX = b.getX() + 4.f;
            const float pillW = b.getWidth() - 8.f;
            const float pillY = isHP ? b.getY() + 3.f : b.getY() + half + 2.f;

            g.setColour(juce::Colour(UI::TOGGLE_ON).withAlpha(0.85f));
            g.fillRoundedRectangle(pillX, pillY, pillW, pillH, 3.f);

            g.setFont(juce::Font(juce::FontOptions("Arial", 13.f, juce::Font::bold)));
            g.setColour(isHP ? juce::Colour(UI::VALUE) : juce::Colour(UI::LABEL));
            g.drawText("HP", b.withHeight(half).toNearestInt(), juce::Justification::centred);
            g.setColour(!isHP ? juce::Colour(UI::VALUE) : juce::Colour(UI::LABEL));
            g.drawText("LP", b.withY(b.getY() + half).withHeight(half).toNearestInt(),
                       juce::Justification::centred);
        }
        else
        {
            const juce::Colour fill = isDown  ? juce::Colour(UI::KNOB_FILL)
                                   : isHover  ? juce::Colour(UI::KNOB_FILL).brighter(0.15f)
                                              : juce::Colour(UI::BTN_BG);
            g.setColour(fill);
            g.fillRoundedRectangle(b, 5.f);
            g.setColour(juce::Colour(UI::BORDER_HI));
            g.drawRoundedRectangle(b, 5.f, 1.5f);
        }
    }

    void drawButtonText(juce::Graphics& g, juce::TextButton& btn, bool, bool) override
    {
        if (btn.getComponentID() == "filter_toggle") return;
        g.setColour(juce::Colour(UI::BTN_TEXT));
        g.setFont(juce::Font(juce::FontOptions("Arial", 14.f, juce::Font::bold)));
        g.drawText(btn.getButtonText(), btn.getLocalBounds(), juce::Justification::centred);
    }

    // ── TextEditor border ──────────────────────────────────────────────────────
    void drawTextEditorOutline(juce::Graphics& g, int w, int h, juce::TextEditor& te) override
    {
        const bool focused = te.hasKeyboardFocus(true);
        g.setColour(focused ? juce::Colour(UI::KNOB_FILL) : juce::Colour(UI::BORDER));
        g.drawRoundedRectangle(0.5f, 0.5f, w - 1.f, h - 1.f, 5.f, 1.5f);
    }

    void fillTextEditorBackground(juce::Graphics& g, int w, int h, juce::TextEditor&) override
    {
        g.setColour(juce::Colour(UI::INPUT_BG));
        g.fillRoundedRectangle(0.f, 0.f, (float)w, (float)h, 5.f);
    }
};
