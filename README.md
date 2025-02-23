# Nabu Voice Notes

**Nabu Voice Notes** is an open-source application designed for secure and private voice-based note-taking. Inspired by the ancient Mesopotamian god of writing and wisdom, Nabu empowers users to capture their thoughts and insights effortlessly while ensuring complete control over their data.

## Usage

You can use the app online at [nabu.apiad.net](https://nabu.apiad.net) or install the latest Android APK in the releases section.

**NOTE:** While both clients share the same backend, there is no cloud-based backup of notes. This means if you log in with the same user in different devices, you will see and spend the same credits, but you will not see the same notes. This is by-design and will not change in the future. Nabu is privacy-first. If you want to sync your notes across devices, I will at some point implement a syncronization feature that doesn't depend on cloud storage.

## Features

Nabu is right now in development, alpha stage. These are the planned features.

### Roadmap

- **Local Storage**: All voice recordings, transcriptions, and post-processed notes are stored securely on your device, ensuring that your notes remain private and are never stored in the cloud.

- **Secure Server-Side Processing**: The app utilizes server-side processing solely for transcription and intermediary tasks, with no final information retained on the server, prioritizing user privacy.

- **Fully Open Source**: Nabu Voice Notes is completely open source, allowing you to download, modify, and run your own version of the app without any cost. You can also host your own server for transcription and processing if desired (see [License](#license) for details).

- **Customizable Note Processing**: Create custom prompts to apply various post-processing features to your notes. This can include tasks like summarization, actionable item extraction, and follow-up question generation, allowing you to tailor how your notes are processed based on your specific needs. By default, three modules are provided:

  - **Actionable Item Extraction**: Automatically extracts actionable items from your notes and presents them as bullet points at the end of each entry.

  - **Follow-Up Questions Generation**: Generates relevant follow-up questions based on the content of your notes to encourage deeper reflection.

  - **Summary Generation**: Provides brief summaries for longer notes, making it easier to review key points quickly.

- **Seamless Server Switching**: Easily switch between official servers and personal servers within the same app without losing any notes. If you run out of credits, all your current notes and local use remain intact—you don’t lose anything.

## License

Nabu Voice Notes is licensed **Creative Commons 4.0 BY-SA-NC** for open-source use, allowing you to run the software privately for individual, educational, or non-profit purposes, with attribution required, and share-alike.

In for-profit organizations or for any form of commercial use, you must install the official app and utilize the official servers.

## Pricing

The official version of Nabu Voice Notes is a free-to-install Android app that operates on a pay-per-use model. Users purchase credits that last indefinitely; there are no subscriptions or recurring costs involved.

Credit packages are bundled in different sizes, with larger bundles offering significant discounts. Please note that credits are prepaid and non-refundable. During the beta phase, all new users will begin with 100 free credits to explore the app's features.

For reference, a typical note of about 500-1000 words, with a basic post-processing such as extracting key insights into bulletpoints, should cost 1 credit.
