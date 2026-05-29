#pragma once
#include <juce_audio_formats/juce_audio_formats.h>
#include <juce_core/juce_core.h>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>

struct WavetableBank
{
    static constexpr int kFrameSize = 2048;

    std::string name;
    int numFrames = 16;
    std::vector<float> data; // numFrames * kFrameSize

    const float* getFrame(int f) const
    {
        const int clamped = juce::jlimit(0, numFrames - 1, f);
        return data.data() + clamped * kFrameSize;
    }

    void getInterpolatedFrame(float pos, float* out) const
    {
        if (data.empty() || numFrames == 0)
        {
            std::fill(out, out + kFrameSize, 0.f);
            return;
        }

        const float fPos = juce::jlimit(0.f, 1.f, pos) * static_cast<float>(numFrames - 1);
        const int   fA   = static_cast<int>(fPos);
        const int   fB   = juce::jmin(fA + 1, numFrames - 1);
        const float frac = fPos - static_cast<float>(fA);

        const float* frameA = getFrame(fA);
        const float* frameB = getFrame(fB);

        for (int i = 0; i < kFrameSize; ++i)
            out[i] = frameA[i] + frac * (frameB[i] - frameA[i]);
    }

    // Loads WAV files from folder; falls back to built-in if none found
    static std::vector<WavetableBank> load(const juce::File& wavetableDir)
    {
        if (wavetableDir.exists() && wavetableDir.isDirectory())
        {
            juce::Array<juce::File> wavFiles;
            wavetableDir.findChildFiles(wavFiles, juce::File::findFiles, false, "*.wav");
            wavFiles.sort();

            if (!wavFiles.isEmpty())
            {
                auto loaded = loadFromFiles(wavFiles);
                if (!loaded.empty())
                    return loaded;
            }
        }
        return createBuiltIn();
    }

private:
    using HList = std::vector<std::pair<float, float>>; // {harmonic_number, amplitude}

    static void fillAdditiveFrame(float* fr, const HList& hl)
    {
        std::fill(fr, fr + kFrameSize, 0.f);
        const float twoPi = 2.f * juce::MathConstants<float>::pi;
        for (int s = 0; s < kFrameSize; ++s)
        {
            const float phase = twoPi * static_cast<float>(s) / static_cast<float>(kFrameSize);
            float sample = 0.f;
            for (const auto& [harm, amp] : hl)
                sample += amp * std::sin(harm * phase);
            fr[s] = sample;
        }
    }

    static void normalise(float* fr)
    {
        float peak = 0.f;
        for (int i = 0; i < kFrameSize; ++i)
            peak = std::max(peak, std::abs(fr[i]));
        if (peak > 1e-6f)
        {
            const float inv = 1.f / peak;
            for (int i = 0; i < kFrameSize; ++i)
                fr[i] *= inv;
        }
    }

    static WavetableBank buildBank(const std::string& bname,
        const HList& kf0, const HList& kf1, const HList& kf2, const HList& kf3)
    {
        WavetableBank bank;
        bank.name = bname;
        bank.numFrames = 16;
        bank.data.resize(static_cast<size_t>(bank.numFrames * kFrameSize), 0.f);

        // Build 4 key frames
        std::vector<float> keyFrames(4 * kFrameSize);
        fillAdditiveFrame(keyFrames.data() + 0 * kFrameSize, kf0);
        fillAdditiveFrame(keyFrames.data() + 1 * kFrameSize, kf1);
        fillAdditiveFrame(keyFrames.data() + 2 * kFrameSize, kf2);
        fillAdditiveFrame(keyFrames.data() + 3 * kFrameSize, kf3);

        normalise(keyFrames.data() + 0 * kFrameSize);
        normalise(keyFrames.data() + 1 * kFrameSize);
        normalise(keyFrames.data() + 2 * kFrameSize);
        normalise(keyFrames.data() + 3 * kFrameSize);

        // Interpolate 16 frames across 4 key frames: keys at positions 0, 5, 10, 15
        const int keyPositions[4] = { 0, 5, 10, 15 };

        for (int frame = 0; frame < 16; ++frame)
        {
            float* dst = bank.data.data() + frame * kFrameSize;

            // Find surrounding key frames
            int kLo = 0, kHi = 1;
            for (int k = 0; k < 3; ++k)
            {
                if (frame >= keyPositions[k] && frame <= keyPositions[k + 1])
                {
                    kLo = k;
                    kHi = k + 1;
                }
            }

            const float span = static_cast<float>(keyPositions[kHi] - keyPositions[kLo]);
            const float frac = span > 0.f
                ? static_cast<float>(frame - keyPositions[kLo]) / span
                : 0.f;

            const float* srcA = keyFrames.data() + kLo * kFrameSize;
            const float* srcB = keyFrames.data() + kHi * kFrameSize;

            for (int s = 0; s < kFrameSize; ++s)
                dst[s] = srcA[s] + frac * (srcB[s] - srcA[s]);
        }

        return bank;
    }

    static std::vector<WavetableBank> createBuiltIn()
    {
        std::vector<WavetableBank> banks;

        // 1. Classic (sine → tri → saw → square)
        {
            HList kf0 = {{1.f, 1.f}};

            // Triangle: odd harmonics 1/n^2, alternating sign
            HList kf1;
            for (int n = 1; n <= 63; n += 2)
            {
                const int k = (n - 1) / 2;
                const float sign = (k % 2 == 0) ? 1.f : -1.f;
                kf1.push_back({static_cast<float>(n), sign / static_cast<float>(n * n)});
            }

            // Sawtooth: harmonics 1/n
            HList kf2;
            for (int n = 1; n <= 64; ++n)
                kf2.push_back({static_cast<float>(n), 1.f / static_cast<float>(n)});

            // Square: odd harmonics 1/n
            HList kf3;
            for (int n = 1; n <= 63; n += 2)
                kf3.push_back({static_cast<float>(n), 1.f / static_cast<float>(n)});

            banks.push_back(buildBank("Classic", kf0, kf1, kf2, kf3));
        }

        // 2. Organ (drawbar)
        {
            HList kf0 = {{1.f, 1.f}};
            HList kf1 = {{1.f, 1.f}, {2.f, 0.9f}, {3.f, 0.5f}};
            HList kf2 = {{1.f, 1.f}, {2.f, 0.9f}, {3.f, 0.7f}, {4.f, 0.6f}, {5.f, 0.4f}, {6.f, 0.4f}};
            HList kf3 = {{1.f, 1.f}, {2.f, 1.f}, {3.f, 0.9f}, {4.f, 0.8f}, {5.f, 0.6f},
                         {6.f, 0.5f}, {8.f, 0.4f}, {10.f, 0.2f}};
            banks.push_back(buildBank("Organ", kf0, kf1, kf2, kf3));
        }

        // 3. Vocal (vowel formants)
        {
            HList kf0 = {{1.f, 0.5f}, {2.f, 0.3f}, {3.f, 0.2f}, {6.f, 1.5f}, {7.f, 1.2f},
                         {8.f, 0.8f}, {11.f, 1.f}, {12.f, 0.7f}};  // A-vowel
            HList kf1 = {{1.f, 0.4f}, {2.f, 0.2f}, {5.f, 0.7f}, {6.f, 0.6f},
                         {14.f, 1.2f}, {15.f, 1.f}, {16.f, 0.7f}};  // E-vowel
            HList kf2 = {{1.f, 1.f}, {2.f, 0.5f}, {3.f, 0.3f}, {4.f, 0.8f},
                         {5.f, 0.6f}, {8.f, 0.7f}, {9.f, 0.4f}};   // O-vowel
            HList kf3 = {{1.f, 1.f}, {2.f, 0.8f}, {3.f, 0.4f}, {4.f, 0.15f}, {5.f, 0.08f}};  // U-vowel
            banks.push_back(buildBank("Vocal", kf0, kf1, kf2, kf3));
        }

        // 4. Metallic
        {
            HList kf0 = {{1.f, 0.8f}, {3.f, 0.7f}, {5.f, 0.6f}, {7.f, 0.5f}, {9.f, 0.4f}, {11.f, 0.3f}};
            HList kf1 = {{2.f, 1.f}, {4.f, 0.8f}, {6.f, 0.6f}, {8.f, 0.5f}, {10.f, 0.4f}};
            HList kf2 = {{1.f, 0.5f}, {3.f, 0.9f}, {6.f, 0.8f}, {9.f, 0.6f}, {12.f, 0.4f}, {15.f, 0.3f}};
            HList kf3 = {{5.f, 1.f}, {8.f, 0.9f}, {11.f, 0.7f}, {14.f, 0.5f}, {17.f, 0.3f}};
            banks.push_back(buildBank("Metallic", kf0, kf1, kf2, kf3));
        }

        // 5. Modern
        {
            // kf0 = saw 16 harmonics
            HList kf0;
            for (int n = 1; n <= 16; ++n)
                kf0.push_back({static_cast<float>(n), 1.f / static_cast<float>(n)});

            HList kf1 = {{1.f, 0.7f}, {2.f, 1.f}, {3.f, 0.5f}, {4.f, 0.8f},
                         {6.f, 0.6f}, {8.f, 0.4f}, {10.f, 0.2f}};
            HList kf2 = {{1.f, 0.5f}, {3.f, 0.8f}, {5.f, 0.9f}, {7.f, 0.7f},
                         {9.f, 0.5f}, {11.f, 0.3f}};
            HList kf3 = {{1.f, 1.f}, {2.f, 0.9f}, {3.f, 0.8f}, {4.f, 0.7f}, {5.f, 0.6f},
                         {6.f, 0.5f}, {7.f, 0.4f}, {8.f, 0.35f}, {9.f, 0.3f}, {10.f, 0.25f},
                         {11.f, 0.2f}, {12.f, 0.18f}, {14.f, 0.15f}, {16.f, 0.12f}};
            banks.push_back(buildBank("Modern", kf0, kf1, kf2, kf3));
        }

        // 6. String
        {
            HList kf0 = {{1.f, 1.f}, {2.f, 0.8f}, {3.f, 0.6f}, {4.f, 0.45f}, {5.f, 0.35f},
                         {6.f, 0.26f}, {7.f, 0.2f}, {8.f, 0.16f}, {9.f, 0.13f}, {10.f, 0.1f}};  // bright pluck
            HList kf1 = {{1.f, 1.f}, {2.f, 0.6f}, {3.f, 0.3f}, {4.f, 0.15f}, {5.f, 0.08f}, {6.f, 0.05f}};  // mellow
            HList kf2 = {{1.f, 1.f}, {2.f, 0.4f}, {3.f, 0.12f}, {4.f, 0.05f}};  // warm
            HList kf3 = {{1.f, 1.f}, {2.f, 0.5f}, {3.f, 0.3f}, {4.f, 0.2f}, {5.f, 0.15f},
                         {6.f, 0.12f}, {7.f, 0.1f}, {8.f, 0.08f}};  // bowed
            banks.push_back(buildBank("String", kf0, kf1, kf2, kf3));
        }

        // 7. Chiptune (Fourier series of pulse waves)
        {
            const float pi = juce::MathConstants<float>::pi;

            // KF0: 12.5% pulse, D=0.125: amp_n = 2/(n*pi)*sin(n*pi*0.125)
            HList kf0;
            for (int n = 1; n <= 63; ++n)
            {
                const float amp = (2.f / (static_cast<float>(n) * pi)) * std::sin(static_cast<float>(n) * pi * 0.125f);
                if (std::abs(amp) > 1e-6f)
                    kf0.push_back({static_cast<float>(n), amp});
            }

            // KF1: 25% pulse, D=0.25: amp_n = 2/(n*pi)*sin(n*pi*0.25)
            HList kf1;
            for (int n = 1; n <= 63; ++n)
            {
                const float amp = (2.f / (static_cast<float>(n) * pi)) * std::sin(static_cast<float>(n) * pi * 0.25f);
                if (std::abs(amp) > 1e-6f)
                    kf1.push_back({static_cast<float>(n), amp});
            }

            // KF2: 50% square, D=0.5 (odd harmonics 1/n)
            HList kf2;
            for (int n = 1; n <= 63; n += 2)
                kf2.push_back({static_cast<float>(n), 1.f / static_cast<float>(n)});

            // KF3: triangle (odd harmonics alternating sign 1/n^2)
            HList kf3;
            for (int n = 1; n <= 63; n += 2)
            {
                const int k = (n - 1) / 2;
                const float sign = (k % 2 == 0) ? 1.f : -1.f;
                kf3.push_back({static_cast<float>(n), sign / static_cast<float>(n * n)});
            }

            banks.push_back(buildBank("Chiptune", kf0, kf1, kf2, kf3));
        }

        return banks;
    }

    static std::vector<WavetableBank> loadFromFiles(const juce::Array<juce::File>& files)
    {
        std::vector<WavetableBank> banks;

        juce::AudioFormatManager formatManager;
        formatManager.registerBasicFormats();

        for (const auto& file : files)
        {
            std::unique_ptr<juce::AudioFormatReader> reader(
                formatManager.createReaderFor(file));

            if (!reader) continue;

            const int totalSamples = static_cast<int>(reader->lengthInSamples);
            if (totalSamples < kFrameSize) continue;

            const int numFrames = totalSamples / kFrameSize;

            WavetableBank bank;
            bank.name = file.getFileNameWithoutExtension().toStdString();
            bank.numFrames = numFrames;
            bank.data.resize(static_cast<size_t>(numFrames * kFrameSize), 0.f);

            juce::AudioBuffer<float> tempBuf(1, totalSamples);
            reader->read(&tempBuf, 0, totalSamples, 0, true, false);

            const float* src = tempBuf.getReadPointer(0);
            for (int f = 0; f < numFrames; ++f)
            {
                float* dst = bank.data.data() + f * kFrameSize;
                std::copy(src + f * kFrameSize, src + f * kFrameSize + kFrameSize, dst);
                normalise(dst);
            }

            banks.push_back(std::move(bank));
        }

        return banks;
    }
};
