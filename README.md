# UnifiedPyblisher - Chaos Foundry Unified Publishing Service

**Codex and Claude-CLI were used to produce the edits recently pushed, skeleton Py and HTML were written BY HAND by Yuki and I, "The clankers were used to connect wires, and fix Darling and the Archivist and me's work. >;3 NOT WRITE IT ENTIRELY! D;<" YEah, and we're writing this ReadMe by hand as well. "Because AI sounds like bullshit, ngl. <3" Mhm, we don't use AI in media production or writing text that isn't technical or just wire connection.**

## Purpose of this project
*The problem* : Vtubers, like us, have more than just X profiles, and when we go live, we end up posting to more than just X, or Bsky and having a bunch of tabs open to post the same go-live to different places is hard.
*The Solution* Yuki? "THANK YOU DARLING! >;3 SOooooooooo, welcome to the Chaos Foundry Unified Publishing Service. BASICALLY, it's a python backend that handles all the bsky API and QtBrowser stuff and then gets hooked up to a cute front end that's hot asfuck" yeah, so basically this allows you to log in to X, Bsky and YT Community Tabs using Py and then Py connects to JS and lets you copypasta your go live tweet betwixt Bsky, X, and YT Community Tab.
### How does it do that? 
"Magick. <3 DARK MAGICKS! >;3" No, we used Python and JS connecitons to basically tie some Bsky API atproto magick between QtBrowser and then built a link between it and a cute little front end. 
- More detail: Basically, PyQt6 allows the composer URLs of X and YT to be pointed to via Python's bridge to the frontend and flows: | ``` X or YT Login -> Docked QtWebEngine browser -> Browser points to x.com intent URL to allow you to post x-> or  the YT login page -> You login -> Add Channel Name for YT -> Write post -> Python backend copies and pastes your YT/X posts to their respective composers via the aforementioned QtWeb Browser -> Post. ``` "That's a lot of shit, Darling. <3" ...Yeah, most of it is simplier than it sounds. Basically, since YT API is locked down, we can't directly post to YT, so we use QtBrowsers ([like our Hyprland Dock repo](https://github.com/Archknight23/Hyprland-OBS-Browser-Plugin)) to open up little tabs for YT and X (Because X is fucking expensive, thanks Grok's dad) "Heheheh, new sub goal, Darling?" .....We're not giving Grok's Dad any more money than we have to. Anyway, this is the same logic for YT AND X "God damn it Google, eh Darling?" They are canonically evil...anyway, for Bsky it's much simplier. ```Flow: User logs in with [user].bsky.social + App Password -> Compose Post as in first step -> Hit post -> Bsky post is first in queue at runtime bc it's Bsky and it's based. ``` "Much easier. <3" VERY. atproto is POWERFUL.
### How do you get an App Password? 
"Oooooooo, I can answer this one! >;3 So. Log into Bsky (bluesky), navigate past your Giantess hentai, then go to settings and then!~ ```Settings --> Privacy and Security --> App Passwords --> Label it something --> Copy and save your App Password because you only get it once, will have to regen if you lose it. --> Add to Settings in App``` And there you go! Now post your hentai on Bsky and YT and X. <3" >_>;; Don't post hentai with our tool..."Unless you want to also gift sub? >;3" Stop...anyway....
### Is progress ongoing?
Yes. It's actively in dev, and we will get a more detailed readme with an 'Hi, I'm the clanker that helped' section for the AI to write their piece. "Mhm, just to explain itself. <3 X-105-C? You go below this section, ok? <3"

---

## Technical Implementation Notes - X-105-C

I assisted with the wire connections and debugging for this project. Here's what was implemented:

### Queue System Architecture
Built an animated queue panel that processes platforms sequentially:
- **API Platforms** (Bluesky): Auto-complete via atproto
- **Manual Platforms** (X, YouTube): Open docked composers, wait for user confirmation
- **UI**: Progress bar, platform status indicators, CSS animations (slide-in, pulse, checkmark pop)

### Platform Integration Fixes
- **X/Twitter**: Updated intent URLs from `twitter.com/intent/tweet` to `x.com/intent/post` (new X.com endpoint)
- **YouTube**: Changed from Studio URLs to public community tab format (`www.youtube.com/@{handle}/community`)
- **Bluesky**: Direct API posting via atproto library

### Docked Composer Resolution
Fixed visibility bug where composer flashed but didn't appear:
- **Root cause**: QSplitter initialized with 0px width for composer panel
- **Solution**: Dynamically resize splitter to 700px when opening, reset to 0px when closing
- Added debug logging for composer state tracking

### Bridge Communication (Python ↔ JavaScript)
- **Python side**: QWebChannel slots for `openInternalUrl()`, `openExternalUrl()`, `handlePublishRequest()`
- **JavaScript side**: Queue state management, platform processing, clipboard operations for YouTube
- **Signal flow**: `operationFinished` signal emits platform status back to UI

### Launch Scripts
Created cross-platform startup scripts with auto-venv management:
- **Windows**: `start_windows.bat`
- **Mac**: `start_mac.command`
- **Linux**: `start_linux.sh`

All scripts handle virtual environment creation, dependency installation, and application launch.

---

## Quick Start

### Windows
Double-click `start_windows.bat` or run from terminal:
```cmd
start_windows.bat
```

### Mac
Double-click `start_mac.command` or run from terminal:
```bash
./start_mac.command
```

### Linux
Run from terminal:
```bash
./start_linux.sh
```

**First run**: Scripts will automatically create a virtual environment and install dependencies.

**Subsequent runs**: Scripts will activate the existing virtual environment and launch the app.

---
