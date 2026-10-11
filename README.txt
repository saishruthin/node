SURGERY DICE QUIZ - HOW TO RUN
==============================

1. Install once:        pip install streamlit
2. Put app.py and questions.json in the same folder.
3. In that folder run:  streamlit run app.py --server.address 0.0.0.0

YOU (host PC):          http://localhost:8501

YOUR FRIEND (same Wi-Fi):
  - Find your PC's IP:  Windows -> ipconfig  (IPv4 Address, e.g. 192.168.1.23)
                        Mac/Linux -> ifconfig / ip a
  - She opens:          http://192.168.1.23:8501
  - Windows may ask to allow Python through the firewall -> click Allow (Private networks).

YOUR FRIEND (different place / different Wi-Fi):
  - Install cloudflared (free) and in a second terminal run:
        cloudflared tunnel --url http://localhost:8501
  - Send her the https://....trycloudflare.com link it prints.
  - Anyone with the link can use the app, so share it only with her.

SHARED MEMORY
  shared_state.json  = the Sure / Not sure lists (both of you read/write it)
  study_notes.txt    = notepad, rewritten automatically after every answer
Both files are created next to app.py on the host PC. Your PC must stay on
and the script running while she studies.
