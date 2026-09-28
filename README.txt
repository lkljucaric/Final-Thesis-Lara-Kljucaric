UPUTE ZA POKRETANJE APLIKACIJE 

1. Instalirati Python.

2. Instalirati Ollama:
   https://ollama.com/

3. Preuzeti potrebne modele u terminalu:

   ollama pull bge-m3
   ollama pull jobautomation/OpenEuroLLM-Croatian

4. Otvoriti mapu projekta u Visual Studio Code-u.

5. Napraviti virtualno okruženje:

   python -m venv .venv

6. Aktivirati virtualno okruženje:

   .venv\Scripts\activate

7. Instalirati potrebne biblioteke:

   pip install flask pandas ollama

8. Pokrenuti aplikaciju:

   python app.py

9. Otvoriti aplikaciju u pregledniku:

   http://127.0.0.1:5000