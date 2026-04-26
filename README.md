# F1 Data Analysis

Dette prosjektet henter data fra en Formel 1 API, analyserer en valgt sesong, og lager både CSV-filer og grafer basert på resultatene.

Flyten er ganske enkel:
- Data hentes fra API
- Dataen bearbeides med pandas
- Resultater lagres lokalt
- Grafer genereres med matplotlib
- Kan også vises i en enkel webapp (Streamlit)

Standard er 2023-sesongen, men du kan velge andre sesonger via kommandolinjen.

Prosjektet bruker Jolpica F1 API:

https://api.jolpi.ca/ergast/f1/

## Oppsett

Installer dependencies:

py -m pip install -r requirements.txt
### Kjøre analyse

Kjør standard sesong (2023):

py .\src\analysis.py

Kjør en spesifikk sesong:

py .\src\analysis.py --season 2022

### Lagre grafer uten å åpne vinduer:

py .\src\analysis.py --no-show

### Kjøre webapp

 Start Streamlit-appen:

py -m streamlit run .\src\app.py

Åpne lenken som vises i terminalen.