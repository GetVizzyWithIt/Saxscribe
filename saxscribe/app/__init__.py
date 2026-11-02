"""The Saxscribe app: a small local web page on top of the pipeline.

    python -m saxscribe app

Upload a recording, get sheet music back (PDF, MusicXML, MIDI), and play
along with the score scrolling in time with the recording. The server runs on
the Mac and the page opens in any browser on the home network, so it works
on an iPad on the music stand.

  library.py     uploads, the transcription queue, and each take's status
  score_view.py  the score for the page (Verovio SVG), its timing map, and the
                 written part for another horn when asked
  server.py      the web server (FastAPI) and its routes
  static/        the two pages: the library and the play-along

The app adds no analysis of its own. It runs pipeline.transcribe() and shows
what the four layers wrote, so a take folder made here is the same as one
made from the command line.
"""
