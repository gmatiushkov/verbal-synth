#pragma once
#include <juce_audio_basics/juce_audio_basics.h>

// Обёртка juce::ADSR с логарифмическим маппингом времён из нормализованных [0..1]
class AdsrEnvelope
{
public:
    void prepare(double sampleRate);
    void reset();

    // attack/decay/release [0..1] → логарифм; sustain [0..1] → линейно
    void applyParams(float attack, float decay, float sustain, float release);

    void noteOn();
    void noteOff();

    bool isActive() const { return mAdsr.isActive(); }

    // Возвращает следующий сэмпл огибающей [0..1]
    float getNextSample() { return mAdsr.getNextSample(); }

    // Умножает блок samples[0..numSamples-1] на огибающую
    void applyToBlock(float* samples, int numSamples);

private:
    juce::ADSR            mAdsr;
    juce::ADSR::Parameters mParams;

    static float logTime(float norm, float minSec, float maxSec);
};
