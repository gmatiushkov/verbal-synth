#pragma once
#include <juce_graphics/juce_graphics.h>

namespace UI
{
    // Background / structure
    inline constexpr juce::uint32 BG        = 0xff080c12;
    inline constexpr juce::uint32 PANEL     = 0xff0d1620;
    inline constexpr juce::uint32 BORDER    = 0xff1e3a50;
    inline constexpr juce::uint32 BORDER_HI = 0xff2e5a78;

    // Text
    inline constexpr juce::uint32 TITLE     = 0xff60d8c0;
    inline constexpr juce::uint32 LABEL     = 0xff4a7090;
    inline constexpr juce::uint32 VALUE     = 0xffd0ecff;

    // Knob / slider
    inline constexpr juce::uint32 KNOB_BG   = 0xff0a1820;
    inline constexpr juce::uint32 KNOB_TRACK= 0xff162535;
    inline constexpr juce::uint32 KNOB_FILL = 0xff00907c;
    inline constexpr juce::uint32 KNOB_THUMB= 0xffe8b840;

    // LFO LED
    inline constexpr juce::uint32 LED_DIM   = 0xff012820;
    inline constexpr juce::uint32 LED_ON    = 0xff00e8a0;

    // Filter toggle
    inline constexpr juce::uint32 TOGGLE_BG = 0xff081420;
    inline constexpr juce::uint32 TOGGLE_ON = 0xff00907c;

    // Text input / button
    inline constexpr juce::uint32 INPUT_BG  = 0xff0a1828;
    inline constexpr juce::uint32 BTN_BG    = 0xff0a2030;
    inline constexpr juce::uint32 BTN_TEXT  = 0xff00e8c8;

    // ADSR preview
    inline constexpr juce::uint32 ADSR_BG   = 0xff050e18;
    inline constexpr juce::uint32 ADSR_LINE = 0xff00d8b0;
    inline constexpr juce::uint32 ADSR_FILL = 0x2200c090;
}
