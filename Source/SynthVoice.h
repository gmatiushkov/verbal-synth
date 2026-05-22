#pragma once
#include <juce_audio_basics/juce_audio_basics.h>
#include "SynthParameters.h"
#include "Oscillator.h"
#include "NoiseGenerator.h"
#include "SynthFilter.h"
#include "AdsrEnvelope.h"

class SynthVoice
{
public:
    void prepare(double sampleRate, int blockSize);

    // Захватывает снимок патча, сбрасывает огибающую, запускает ноту
    void noteOn(int midiNote, int velocity, const SynthPatch& patch);

    // Переводит огибающую в фазу release; голос живёт до конца затухания
    void noteOff();

    // false только после полного затухания ADSR
    bool isActive() const;

    int getCurrentNote() const { return mNote; }

    // Добавляет аудио голоса к обоим каналам buffer
    void renderNextBlock(juce::AudioBuffer<float>& buffer,
                         int startSample, int numSamples,
                         const float* lfoValues);

    // Обновляет нетриггерные параметры (фильтр, LFO, уровни) на лету
    void updatePatch(const SynthPatch& patch);

private:
    Oscillator     mOsc1, mOsc2;
    NoiseGenerator mNoise;
    SynthFilter    mFilter;
    AdsrEnvelope   mEnv;

    SynthPatch mPatch;

    int    mNote       = 60;
    bool   mNoteIsOn   = false;
    double mSampleRate = 44100.0;
    int    mBlockSize  = 512;

    std::vector<float> mMonoBuf;

    float computeOscFreq(float octaveNorm, float detuneNorm) const;
};
