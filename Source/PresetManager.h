#pragma once
#include <juce_core/juce_core.h>
#include "SynthParameters.h"

class PresetManager
{
public:
    struct PresetInfo
    {
        juce::String name;
        juce::File   file;
    };

    void setFolder(const juce::File& dir)
    {
        mFolder = dir;
        if (!mFolder.exists())
            mFolder.createDirectory();
        rescan();
    }

    void rescan()
    {
        mPresets.clear();
        if (!mFolder.isDirectory()) return;

        for (const auto& f : mFolder.findChildFiles(juce::File::findFiles, false, "*.json"))
            mPresets.add({ f.getFileNameWithoutExtension(), f });

        struct Cmp {
            static int compareElements(const PresetInfo& a, const PresetInfo& b)
            { return a.name.compareIgnoreCase(b.name); }
        } cmp;
        mPresets.sort(cmp, true);
    }

    int numPresets() const { return mPresets.size(); }

    const PresetInfo& getInfo(int index) const { return mPresets.getReference(index); }

    int findByName(const juce::String& name) const
    {
        for (int i = 0; i < mPresets.size(); ++i)
            if (mPresets[i].name.equalsIgnoreCase(name))
                return i;
        return -1;
    }

    SynthPatch loadPreset(int index) const
    {
        SynthPatch patch;
        const juce::String text = mPresets[index].file.loadFileAsString();
        const juce::var    parsed = juce::JSON::parse(text);
        if (!parsed.isObject()) return patch;

        auto* dynObj = parsed.getDynamicObject();
        if (!dynObj) return patch;

        float* vals = patch.data();
        const auto names = SynthPatch::paramNames();
        for (int i = 0; i < SynthPatch::kNumParams; ++i)
        {
            const juce::Identifier key(names[i].data());
            if (dynObj->hasProperty(key))
                vals[i] = juce::jlimit(0.f, 1.f,
                    static_cast<float>(static_cast<double>(dynObj->getProperty(key))));
        }
        return patch;
    }

    void savePreset(const juce::String& name, const SynthPatch& patch)
    {
        auto* obj = new juce::DynamicObject();
        const auto  names = SynthPatch::paramNames();
        const float* vals = patch.data();
        for (int i = 0; i < SynthPatch::kNumParams; ++i)
            obj->setProperty(juce::Identifier(names[i].data()), static_cast<double>(vals[i]));

        const juce::String json = juce::JSON::toString(juce::var(obj), true);
        mFolder.getChildFile(name + ".json").replaceWithText(json);
        rescan();
    }

private:
    juce::File              mFolder;
    juce::Array<PresetInfo> mPresets;
};
