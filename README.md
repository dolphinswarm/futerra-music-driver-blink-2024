# FuTerra | I Was The Earth - Music Driver

The **FuTerra | I Was The Earth Music Driver** is the generative system used to power the music for the _FuTerra | I Was The Earth_ installation at [BLINK 2024](https://www.blinkcincinnati.com/) in Cincinnati, OH by &FRIENDS. The goal of the system is to infinitely and randomly generate music, which evolves with the changing visuals of the installation.

![FuTerra | I Was The Earth](/assets/futerra.jpg)

An audio preview of the system can be found in the `/assets` folder.

> ⚠️ As a note - due to the specific plugins and setup of Ableton, this project is meant as more of an archive than something that can be pulled and run.

## Table of Contents

-   [Music Design](#music-design)
-   [Core Technologies](#core-technologies)
-   [The Music Algorithm](#the-music-algorithm)
-   [Future Improvements](#future-improvements)

## Music Design

When it came to writing a generative system, there were a few design considerations for how to get the music to sound as we wanted:

-   The biggest thing with making a "random" music system is making it not feel random, i.e., not like a 5-year-old banging on a piano. Truly random music would be incredibly jarring and janky, and would take people out of the meditative experience that we wanted the installation to have. Thus, a large part of the system is setting up rules to make chord and key transitions as natural as possible.
-   We wanted a "sound bath" / meditative style to the music, which meant lots of sustained notes that change while held out. This means lots of automated audio effects (i.e., Auto Filter, Auto Pan, etc.) and evolving synth pads, which meant we could do less MIDI / music triggers. Additionally, to make chord transitions less jarring, we wanted to make it so no unnecessary re-triggers were done.
-   With a system like this, inter-change triggers needed special considerations; this includes things like bells, melodies, etc. This meant doing some creative things, like having MIDI clip-based melodies and using arpeggiators with randomness to play bells.
-   Part of the immersion of a system like this too is with sound effects, and needing a system to play ambient sounds for the various scenes.
-   Evolution of the music involved changing with the scene, which mainly was the time of day in the window. This was handled via separate "scenes" in Ableton, which use a TD-powered equal-power crossfade to transition between scenes.

More information about the music algorithm can be found below.

## Core Technologies

The music driver is powered through two main components: [_TouchDesigner_](https://derivative.ca/) and [_Ableton_](https://www.ableton.com/), and is mainly driven through their communication plugin called [_TDAbleton_](https://docs.derivative.ca/TDAbleton), which allows for OSC connection between the two programs. In addition, TouchDesigner has custom scripting with Python, which extends the flexibility of TouchDesigner's operators.

The music driver communicates separately with another TouchDesigner project thru OSC, which in turn communicates with the Unreal Engine project to power the visuals of the lights, FuTerra, etc. Note that the Unreal Engine project is stored in a separate private repo instead of this project.

## The Music Algorithm

In general, music system is controlled by a Beat CHOP (essentially, a timer), which every 8 beats triggers a chord (ii, IV) change, a chord variation (sus2, dim, etc.) change, or a key change in the song. Additionally, each beat has a chance to trigger a percussion instrument or pre-defined melody.

In the TouchDesigner program, there is a global storage OP, which stores information about the properties of the song, such as the key, chord, current instrument notes, and more. Each time the music script is triggered by the Beat CHOP, it pulls this information from the global storage. This info, with data from other OPs, determines what the next set of MIDI notes should be, then sends those notes to the respective instruments in all applicable scenes. After this, miscellaneous music handling and cleanup are also performed, including triggering of percussion + melodies, killing instruments that shouldn't be playing, and updating the global store.

Lots of the code in this project involves adjusting notes to the song's current scale mode, key, chord, and chord variation. For example, if I was in the key of F, in Dorian mode, trying to play a iii sus2 chord, I would need to make sure I'm following the structure of this. However, with a basic MIDI math system, it would be like:

`60 (base MIDI note) + 5 (key offset) + base chord note (4) + chord variation note (either 0, 2, or 7)`

In this example, however, the Dorian mode makes the 3rd and 7th flat, so the base chord note doesn't apply; we would need to adjust them to fit in the scale mode. This would also apply for chord variations too; where a I chord in F Dorian would technically be minor and need to be adjusted. Both sustained chords and melodies have to be adjusted to follow this methodology. There is a LOT of code to handle this, which makes it hard to summarize here, so if you're curious check out the code inside the `/python_scripts` folder.

Additionally, code is also present to handle the time of day. This is used locally to determine what scenes should be audible, then is exported via OSC to the other TouchDesigner project to control the time of day in the UE scene's [Ultra-Dynamic Sky](https://www.fab.com/listings/84fda27a-c79f-49c9-8458-82401fb37cfb). This is handled by a collection of Timer OPs, which each trigger a specific moment in the scene (i.e., change in the sky, change in the audio scene, pulling up the credits, etc.)

## Future Improvements

In the event this system needs to be reused or rethought for a future &FRIENDS installation, there are some modifications that could help improve the experience.

-   Rather than making the system reliant on "scenes", each instrument could be controlled by a specific time of day range, allowing for more actually-evolving music instead of crossfades.
-   More musical elements, like harmonies and counter-melodies.
-   Ability to anticipate the "next" transition, which could allow for some interesting musical elements like build-ups
-   More dynamic way to add instruments and audio to the TouchDesigner project
