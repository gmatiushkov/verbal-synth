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
                          juce::Slider&) override
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

        // Thumb dot
        const float tx  = cx + std::sin(fillAngle) * arcR;
        const float ty  = cy - std::cos(fillAngle) * arcR;
        const float dotR = trackThick * 0.65f;
        g.setColour(juce::Colour(UI::KNOB_THUMB));
        g.fillEllipse(tx - dotR, ty - dotR, dotR * 2.f, dotR * 2.f);
    }

    // ── Linear slider ──────────────────────────────────────────────────────────
    void drawLinearSlider(juce::Graphics& g, int x, int y, int w, int h,
                          float sliderPos, float, float,
                          juce::Slider::SliderStyle style, juce::Slider&) override
    {
        if (style == juce::Slider::LinearVertical)
        {
            const float cx     = x + w * 0.5f;
            const float trackW = juce::jmax(3.f, w * 0.08f);
            const float thumbW = juce::jmax(10.f, w * 0.45f);
            const float thumbH = juce::jmax(5.f,  thumbW * 0.26f);

            g.setColour(juce::Colour(UI::KNOB_TRACK));
            g.fillRoundedRectangle(cx - trackW * 0.5f, (float)y, trackW, (float)h, trackW * 0.5f);

            g.setColour(juce::Colour(UI::KNOB_FILL));
            g.fillRoundedRectangle(cx - trackW * 0.5f, sliderPos, trackW,
                                   (float)(y + h) - sliderPos, trackW * 0.5f);

            g.setColour(juce::Colour(UI::KNOB_THUMB));
            g.fillRoundedRectangle(cx - thumbW * 0.5f, sliderPos - thumbH * 0.5f,
                                   thumbW, thumbH, thumbH * 0.5f);
        }
        else if (style == juce::Slider::LinearHorizontal)
        {
            const float cy     = y + h * 0.5f;
            const float trackH = juce::jmax(4.f, h * 0.18f);
            const float thumbH = juce::jmax(16.f, h * 0.65f);
            const float thumbW = juce::jmax(8.f,  thumbH * 0.38f);

            g.setColour(juce::Colour(UI::KNOB_TRACK));
            g.fillRoundedRectangle((float)x, cy - trackH * 0.5f, (float)w, trackH, trackH * 0.5f);

            g.setColour(juce::Colour(UI::KNOB_FILL));
            g.fillRoundedRectangle((float)x, cy - trackH * 0.5f,
                                   sliderPos - x, trackH, trackH * 0.5f);

            g.setColour(juce::Colour(UI::KNOB_THUMB));
            g.fillRoundedRectangle(sliderPos - thumbW * 0.5f, cy - thumbH * 0.5f,
                                   thumbW, thumbH, thumbW * 0.5f);
        }
    }

    int getSliderThumbRadius(juce::Slider&) override { return 0; }

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

            g.setFont(juce::FontOptions(13.f).withStyle("Bold"));
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
        g.setFont(juce::FontOptions(14.f).withStyle("Bold"));
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
