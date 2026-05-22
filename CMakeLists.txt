cmake_minimum_required(VERSION 3.22)
project(VerbalSynth VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory("C:/Root/6 - Dev/JUCE" JUCE)

juce_add_gui_app(VerbalSynth
    PRODUCT_NAME     "VerbalSynth"
    VERSION          "0.1.0"
    COMPANY_NAME     "VerbalSynth"
    BUNDLE_ID        "com.verbalsynth.app"
)

target_sources(VerbalSynth PRIVATE
    Source/Main.cpp
    Source/MainComponent.cpp
    Source/SynthVoice.cpp
    Source/SynthEngine.cpp
    Source/Oscillator.cpp
    Source/AdsrEnvelope.cpp
    Source/SynthFilter.cpp
    Source/LfoGenerator.cpp
    Source/PhaserEffect.cpp
    Source/DelayEffect.cpp
    Source/ReverbEffect.cpp
    Source/PatchPanel.cpp
)

target_compile_definitions(VerbalSynth PRIVATE
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_APPLICATION_NAME_STRING="$<TARGET_PROPERTY:VerbalSynth,JUCE_PRODUCT_NAME>"
    JUCE_APPLICATION_VERSION_STRING="$<TARGET_PROPERTY:VerbalSynth,JUCE_VERSION>"
)

target_link_libraries(VerbalSynth PRIVATE
    juce::juce_audio_basics
    juce::juce_audio_devices
    juce::juce_audio_formats
    juce::juce_audio_processors
    juce::juce_audio_utils
    juce::juce_core
    juce::juce_data_structures
    juce::juce_dsp
    juce::juce_events
    juce::juce_graphics
    juce::juce_gui_basics
    juce::juce_gui_extra
    juce::juce_recommended_config_flags
    juce::juce_recommended_lto_flags
    juce::juce_recommended_warning_flags
)
