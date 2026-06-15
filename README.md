# 📊 Scanner PEA Pro

Application Streamlit de screening et de suivi d'actions pour un PEA (Plan
d'Épargne en Actions), avec scoring quantitatif multi-critères, suivi des
marchés, backtests de stratégies simples et un calculateur de swing trading.

## 1. Installation

Python 3.10+ recommandé.

```bash
# (optionnel mais recommandé) créer un environnement virtuel
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# installer les dépendances
pip install -r requirements.txt
```

## 2. Lancement

```bash
streamlit run app.py
```

L'application s'ouvre dans le navigateur (par défaut sur
`http://localhost:8501`).

## 3. Format du fichier CSV à charger

Le fichier CSV doit contenir au minimum les colonnes suivantes :

| Colonne  | Obligatoire | Description                                   |
|----------|-------------|------------------------------------------------|
| `Nom`    | Oui         | Nom affiché de l'action                         |
| `Ticker` | Oui         | Symbole Yahoo Finance (ex. `MC.PA`, `AAPL`)     |
| `Marché` | Non         | Libellé libre (CAC40, SBF120…) — `PEA` si absent |

Un bouton **"📄 Exemple de CSV"** dans le panneau latéral permet de
télécharger un fichier modèle.

⚠️ Le ticker doit correspondre exactement au symbole utilisé par Yahoo
Finance (les actions cotées à Paris se terminent généralement par `.PA`).

## 4. Configuration Telegram

À la fin de chaque scan, un récapitulatif du classement (Top N ou
classement complet, au choix dans la barre latérale) est généré en PDF et
envoyé sur Telegram.

Pour configurer votre propre bot, ouvrez `app.py` et renseignez en haut du
fichier :

```python
TELEGRAM_TOKEN   = "VOTRE_TOKEN_DE_BOT"
TELEGRAM_CHAT_ID = VOTRE_CHAT_ID
```

- `TELEGRAM_TOKEN` : créé via [@BotFather](https://t.me/BotFather) sur Telegram.
- `TELEGRAM_CHAT_ID` : identifiant numérique de la conversation/chat cible
  (peut être obtenu via le bot [@userinfobot](https://t.me/userinfobot)).

Si l'envoi échoue (pas de connexion, identifiants invalides…), un avertissement
est affiché dans la barre latérale mais le scan reste utilisable normalement.

## 5. Onglets de l'application

- **🏆 Classement** : classement des actions scannées, trié par un score
  combiné (70% Score PEA /100 + 30% performance du dernier mois normalisée).
  Filtres par catégorie, marché et recherche libre. Export du classement
  filtré en CSV ou PDF. Cliquez sur une ligne pour afficher la fiche complète
  de l'action (analyse fondamentale, actualités, cotation, tendance,
  graphique interactif, et détail du calcul du score).
- **🔍 Recherche** : recherche libre d'une action par nom ou ticker parmi
  toutes les actions du fichier CSV, qu'elles aient été scannées ou non.
- **🌐 Suivi Marché Global** : suivi des grands indices (CAC 40, SBF 120,
  STOXX 600, S&P 500, Nasdaq, Euro Stoxx 50, DAX, PEA-PME), graphique
  comparatif normalisé (base 100), et plus fortes variations du jour parmi
  les actions scannées.
- **📈 Backtest** : test de stratégies simples (croisement de moyennes
  mobiles, prix vs MM200, RSI, breakout) sur une action choisie, avec
  comparaison à une stratégie "Buy & Hold".
- **💱 Swing Trading** : calcul de plus-value/perte potentielle à partir
  d'un PRU, d'un Stop Loss et de jusqu'à trois objectifs de Take Profit.

## 6. Méthodologie du Score PEA /100

Le score combine **9 piliers** pondérés, chacun calculé en convertissant
plusieurs métriques brutes en **percentile** par rapport aux autres actions
du scan en cours (0 = pire de la liste, 100 = meilleure) :

| Pilier                       | Poids |
|-------------------------------|------|
| 🏛️ Qualité / Fondamentaux     | 25 % |
| 💰 Valorisation                | 15 % |
| 🌱 Croissance                  | 10 % |
| 🚀 Momentum Prix               | 15 % |
| 📈 Technique & Flux            | 10 % |
| 🔁 Révisions de bénéfices      | 10 % |
| 🛡️ Risque                      | 10 % |
| 🗞️ Sentiment                   | 3 %  |
| 🌍 Macro & Secteur             | 2 %  |

Des **pénalités** sont ensuite déduites du score final dans certains cas :
BPA prévisionnel en forte baisse, Free Cash Flow négatif sur les exercices
disponibles, endettement excessif (Dette/Fonds propres), ou rupture de la
moyenne mobile à 200 jours combinée à une sous-performance sectorielle.

### Catégories

| Score    | Catégorie       |
|----------|-----------------|
| > 90     | 🟣 Élite         |
| 80 – 90  | 🟢 Achat Fort    |
| 70 – 80  | 🟢 Achat         |
| 60 – 70  | 🟡 Surveiller    |
| 50 – 60  | ⚪ Neutre         |
| 40 – 50  | 🟠 Faible        |
| < 40     | 🔴 À éviter      |

Le détail complet du calcul (valeur de chaque métrique, percentile,
points forts/faibles, pénalités appliquées) est disponible pour chaque
action dans l'onglet **"🎯 Explication du Score"** de sa fiche détaillée.

> ⚠️ Le score étant basé sur des **percentiles relatifs aux actions du scan
> en cours**, il dépend de la composition du fichier CSV chargé : une même
> action peut obtenir un score différent selon les autres actions analysées
> en même temps.

## 7. Notes & limitations

- Les données proviennent de **Yahoo Finance** via `yfinance` : disponibilité
  et fraîcheur des données fondamentales varient selon les tickers, et
  certaines métriques peuvent être absentes (affichées comme "Non
  disponible").
- En cas d'erreur réseau ponctuelle (rate-limit Yahoo, coupure...),
  l'application retente automatiquement quelques fois avant d'abandonner.
- Le bouton **"🧹 Vider le cache de données"** dans la barre latérale force
  le rechargement de toutes les données (cours, indices, fondamentaux).
- La description des sociétés est traduite automatiquement de l'anglais
  vers le français via un service public de traduction ; si ce service est
  injoignable, le texte original en anglais est affiché.
- Cette application est un outil d'aide à l'analyse et **ne constitue pas un
  conseil en investissement**.
