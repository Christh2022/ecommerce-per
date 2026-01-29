# Dashboard E-commerce Analytics

Dashboard interactif de visualisation et d'analyse pour données e-commerce avec simulation de tests A/B intégrée.

## Description

Application web interactive développée avec Dash et Plotly permettant l'analyse complète de données e-commerce. Le dashboard propose six pages d'analyse avec plus de 25 visualisations interactives, des KPIs en temps réel, et un simulateur de tests A/B avec calculs statistiques avancés.

## Fonctionnalités principales

### Pages d'analyse

- **Vue d'ensemble** : KPIs globaux, indicateurs de performance clés, évolution des métriques
- **Performance** : Analyse temporelle, heatmaps, distribution des événements, tendances hebdomadaires
- **Utilisateurs** : Segmentation, engagement, analyse cohortes, comportement par jour de semaine
- **Produits** : Top produits, matrice de performance, analyse comparative via treemap
- **Funnel de conversion** : Analyse détaillée du parcours utilisateur, taux de drop-off, recommandations
- **Tests A/B** : Simulateur interactif avec calculs statistiques complets

### Visualisations

- Graphiques en barres, lignes et aires empilées
- Heatmaps de performance temporelle
- Treemap pour analyse hiérarchique des produits
- Matrices de corrélation et scatter plots
- Graphiques en entonnoir (funnel charts)
- Indicateurs de distribution et histogrammes

### Fonctionnalités techniques

- Filtres de dates dynamiques basés sur les données réelles
- Thème sombre (Bootstrap DARKLY) avec cohérence visuelle
- Mise en cache des données pour optimisation des performances
- Architecture modulaire avec callbacks Dash
- Navigation par sidebar fixe
- Responsive design adaptatif

## Structure du projet

```
perside-dataset-ecommerce/
├── data/
│   ├── raw/                          # Données sources brutes
│   │   ├── events.csv
│   │   ├── category_tree.csv
│   │   ├── item_properties_part1.csv
│   │   └── item_properties_part2.csv
│   └── clean/                        # Données nettoyées et enrichies
│       ├── events_enriched.csv
│       ├── user_features.csv
│       ├── product_features.csv
│       └── ab_test_results.json
├── outputs/                          # Graphiques et exports
├── dashboard_app.py                  # Application principale Dash
├── eda_analysis.py                   # Analyse exploratoire des données
├── eda_retailrocket.py              # Analyse spécifique RetailRocket
├── ab_testing_scenarios.py          # Générateur de scénarios A/B
├── simulate_ab_test_from_data.py    # Simulation A/B depuis données réelles
├── test_dashboard_integration.py    # Tests d'intégration
├── requirements.txt                 # Dépendances Python
└── README.md                        # Ce fichier
```

## Installation

### Prérequis

- Python 3.12 ou supérieur
- pip (gestionnaire de paquets Python)
- 2 Go de RAM minimum
- Espace disque : 500 Mo pour données et dépendances

### Récupération des données

Le projet utilise le dataset RetailRocket disponible sur Kaggle :

1. Créer un compte sur [Kaggle](https://www.kaggle.com) si nécessaire

2. Télécharger le dataset RetailRocket :
   - URL : https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset
   - Ou via Kaggle CLI :
   ```bash
   kaggle datasets download -d retailrocket/ecommerce-dataset
   ```

3. Extraire les fichiers dans le dossier `data/raw/` :
   ```bash
   unzip ecommerce-dataset.zip -d data/raw/
   ```

4. Structure attendue après extraction :
   ```
   data/raw/
   ├── events.csv                    # 2.7M événements utilisateurs
   ├── category_tree.csv             # Hiérarchie des catégories
   ├── item_properties_part1.csv     # Propriétés produits (partie 1)
   └── item_properties_part2.csv     # Propriétés produits (partie 2)
   ```

Note : Si les fichiers de données ne sont pas présents, le dashboard générera automatiquement des données de démonstration pour tester l'application.

### Étapes d'installation

1. Cloner ou télécharger le projet

```bash
cd perside-dataset-ecommerce
```

2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv
```

3. Activer l'environnement virtuel

Windows :

```bash
venv\Scripts\activate
```

Linux/Mac :

```bash
source venv/bin/activate
```

4. Installer les dépendances

```bash
pip install -r requirements.txt
```

### Préparation des données

Avant de lancer le dashboard, il est nécessaire de générer les fichiers de données nettoyées :

1. Assurez-vous que les fichiers bruts sont dans `data/raw/` (voir section "Récupération des données")

2. Exécuter le script de nettoyage et d'enrichissement des données :

```bash
python eda_analysis.py
```

Ce script va :
- Charger les données brutes depuis `data/raw/`
- Nettoyer et enrichir les événements utilisateurs
- Calculer les features agrégées par utilisateur et par produit
- Générer les fichiers dans `data/clean/` :
  - `events_enriched.csv` : Événements avec variables dérivées
  - `user_features.csv` : Caractéristiques par utilisateur
  - `product_features.csv` : Caractéristiques par produit
  - `category_hierarchy.csv` : Hiérarchie des catégories

Durée estimée : 5-15 minutes selon la taille des données

Note : Si ce script n'est pas exécuté, le dashboard générera automatiquement des données de démonstration.

## Utilisation

### Lancement du dashboard

1. Activer l'environnement virtuel

2. S'assurer que les données ont été préparées (voir "Préparation des données")

3. Lancer l'application

```bash
python dashboard_app.py
```

4. Ouvrir le navigateur à l'adresse

```
http://localhost:8050/
```

### Navigation

- Utilisez le menu latéral gauche pour naviguer entre les pages
- Sélectionnez les dates via les filtres en haut de chaque page
- Survolez les graphiques pour afficher les détails interactifs
- Cliquez sur les légendes pour activer/désactiver des séries

### Simulation de tests A/B

1. Accéder à la page "Tests A/B" via le menu
2. Remplir le formulaire de simulation :
   - Nom du test
   - Durée en jours
   - Lift attendu (%)
   - Noms des groupes A et B
   - Taux de conversion de base
   - Taille d'échantillon par groupe
3. Cliquer sur "Lancer la Simulation"
4. Consulter les résultats statistiques et l'impact business

## Structure des données

### Fichiers de données attendus

#### events.csv

Événements utilisateurs bruts du site e-commerce.

Colonnes :

- `timestamp` : Date et heure de l'événement
- `visitorid` : Identifiant unique du visiteur
- `event` : Type d'événement (view, addtocart, transaction)
- `itemid` : Identifiant du produit
- `transactionid` : ID de transaction (si applicable)

#### category_tree.csv

Hiérarchie des catégories de produits.

Colonnes :

- `categoryid` : Identifiant de catégorie
- `parentid` : Catégorie parente

#### item_properties_part1.csv et item_properties_part2.csv

Propriétés des produits (métadonnées).

Colonnes :

- `timestamp` : Date de mise à jour
- `itemid` : Identifiant du produit
- `property` : Nom de la propriété
- `value` : Valeur de la propriété

### Données générées

#### events_enriched.csv

Données d'événements enrichies avec features calculées.

Colonnes supplémentaires :

- `session_id` : Session de navigation
- `hour` : Heure de l'événement
- `day_of_week` : Jour de la semaine
- `is_weekend` : Indicateur weekend
- Features comportementales diverses

#### user_features.csv

Caractéristiques agrégées par utilisateur.

Colonnes :

- `visitorid` : Identifiant utilisateur
- `total_views` : Nombre total de vues
- `total_addtocart` : Nombre d'ajouts au panier
- `total_transactions` : Nombre de transactions
- `conversion_rate` : Taux de conversion
- `avg_session_duration` : Durée moyenne de session
- `recency_days` : Jours depuis dernière visite
- `user_segment` : Segment utilisateur (High Value, Regular, New, Inactive)

#### product_features.csv

Caractéristiques agrégées par produit.

Colonnes :

- `itemid` : Identifiant produit
- `total_views` : Nombre total de vues
- `total_addtocart` : Nombre d'ajouts au panier
- `total_transactions` : Nombre de ventes
- `conversion_rate` : Taux de conversion produit
- `avg_views_per_user` : Vues moyennes par utilisateur
- `popularity_score` : Score de popularité

#### ab_test_results.json

Résultats de simulations de tests A/B.

Structure :

```json
{
  "test_name": "Nom du test",
  "test_date": "2026-01-29",
  "duration_days": 14,
  "group_A": {
    "name": "Contrôle",
    "n_users": 1000,
    "n_conversions": 50,
    "conversion_rate": 0.05
  },
  "group_B": {
    "name": "Variante",
    "n_users": 1000,
    "n_conversions": 75,
    "conversion_rate": 0.075
  },
  "statistics": {
    "absolute_lift": 0.025,
    "relative_lift": 50.0,
    "z_score": 2.58,
    "p_value": 0.0099,
    "significant": true,
    "ci_lower": 0.005,
    "ci_upper": 0.045,
    "power": 0.85
  },
  "business_impact": {
    "monthly_users": 100000,
    "additional_conversions_month": 2500,
    "additional_revenue_month": 250000,
    "additional_revenue_year": 3000000,
    "roi_percent": 500,
    "payback_months": 2
  }
}
```

## Technologies utilisées

### Framework principal

- **Dash 2.14.2** : Framework web pour applications Python interactives
- **Dash Bootstrap Components 1.5.0** : Composants UI Bootstrap pour Dash
- **Plotly 5.18.0** : Bibliothèque de visualisation interactive

### Traitement de données

- **Pandas 2.1.4** : Manipulation et analyse de données tabulaires
- **NumPy 1.26.2** : Calcul numérique et manipulation de tableaux

### Visualisation

- **Matplotlib 3.8.2** : Création de graphiques statiques
- **Seaborn 0.13.0** : Visualisations statistiques avancées

### Analyse statistique

- **SciPy 1.11.4** : Tests statistiques (z-test, t-test, intervalles de confiance)
- **Scikit-learn 1.3.2** : Machine learning et analyse prédictive

### Performance et optimisation

- **Flask-Caching 2.1.0** : Système de cache pour accélération
- **Redis 5.0.1** : Cache distribué (optionnel, pour production)

### Production (optionnel)

- **Gunicorn 21.2.0** : Serveur WSGI pour déploiement
- **PostgreSQL / psycopg2-binary 2.9.9** : Base de données relationnelle
- **Python-dotenv 1.0.0** : Gestion des variables d'environnement

### Tests

- **Pytest 7.4.3** : Framework de tests unitaires
- **Pytest-cov 4.1.0** : Couverture de code

## Configuration

### Variables d'environnement

Créer un fichier `.env` à la racine du projet (optionnel) :

```env
# Configuration Dashboard
DASH_HOST=localhost
DASH_PORT=8050
DASH_DEBUG=True

# Cache
CACHE_TYPE=simple
CACHE_TIMEOUT=300

# Base de données (optionnel)
DATABASE_URL=postgresql://user:password@localhost:5432/ecommerce

# Redis (optionnel)
REDIS_URL=redis://localhost:6379/0
```

### Personnalisation du thème

Dans `dashboard_app.py`, ligne 36 :

```python
external_stylesheets=[dbc.themes.DARKLY, dbc.icons.FONT_AWESOME]
```

Thèmes disponibles : DARKLY, CYBORG, SLATE, SUPERHERO, SOLAR, VAPOR (sombres)
Ou FLATLY, COSMO, LITERA, MINTY, PULSE (clairs)

### Configuration du cache

Ligne 44-47 de `dashboard_app.py` :

```python
cache = Cache(app.server, config={
    'CACHE_TYPE': 'simple',  # ou 'redis' pour production
    'CACHE_DEFAULT_TIMEOUT': 300  # Durée en secondes
})
```

## Déploiement en production

### Option 1 : Serveur local avec Gunicorn

```bash
gunicorn dashboard_app:server -b 0.0.0.0:8050 -w 4
```

### Option 2 : Docker

Créer un `Dockerfile` :

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050

CMD ["gunicorn", "dashboard_app:server", "-b", "0.0.0.0:8050", "-w", "4"]
```

Construire et lancer :

```bash
docker build -t ecommerce-dashboard .
docker run -p 8050:8050 ecommerce-dashboard
```

### Option 3 : Hébergement cloud

- **Heroku** : Compatible avec buildpack Python
- **AWS Elastic Beanstalk** : Déploiement avec configuration Python
- **Google Cloud Run** : Conteneurisation avec Cloud Build
- **Azure App Service** : Support natif Python/Flask

## Calculs statistiques

### Tests A/B

Le simulateur implémente les calculs suivants :

#### Z-test pour proportions

```
z = (p_B - p_A) / sqrt(p_pooled * (1 - p_pooled) * (1/n_A + 1/n_B))
```

Où :

- `p_A`, `p_B` : taux de conversion des groupes A et B
- `p_pooled` : proportion poolée (moyenne pondérée)
- `n_A`, `n_B` : tailles des échantillons

#### P-value

Calculée via la distribution normale standard (test bilatéral) :

```
p_value = 2 * (1 - norm.cdf(abs(z_score)))
```

#### Intervalle de confiance à 95%

```
CI = (p_B - p_A) ± 1.96 * SE
```

Où SE est l'erreur standard de la différence.

#### Puissance statistique

Probabilité de détecter un effet s'il existe réellement.

```
power = 1 - beta
```

Calculée via la distribution normale non-centrale.

#### Lift relatif

```
relative_lift = ((p_B - p_A) / p_A) * 100
```

### Impact business

Projections basées sur les résultats statistiques :

- Conversions additionnelles mensuelles : `monthly_users * absolute_lift`
- Revenu additionnel annuel : `conversions * avg_order_value * 12`
- ROI : `(revenu_additionnel - coût_implémentation) / coût_implémentation * 100`

## Métriques et KPIs

### Définitions

- **Taux de conversion** : (Transactions / Vues uniques) \* 100
- **Taux d'ajout au panier** : (AddToCart / Vues) \* 100
- **Taux d'abandon de panier** : (AddToCart - Transactions) / AddToCart \* 100
- **Panier moyen** : Revenu total / Nombre de transactions
- **Engagement utilisateur** : Total événements / Utilisateurs uniques
- **Taux de rebond** : Sessions d'une seule page / Total sessions \* 100
- **RFM Score** : Recency + Frequency + Monetary (segmentation client)

### Segments utilisateurs

- **High Value** : Conversion rate > 10% ET transactions > 5
- **Regular** : Conversion rate 3-10% OU transactions 2-5
- **New** : Moins de 7 jours d'ancienneté
- **Inactive** : Plus de 30 jours sans activité

## Performances

### Optimisations implémentées

- Mise en cache des dataframes avec décorateur `@cache.memoize()`
- Chargement paresseux des données par page
- Suppression des callbacks non utilisés
- Limitation des données affichées dans les tableaux
- Utilisation de types de données optimisés (categorical, int32)

### Temps de chargement attendus

- Première visite : 2-5 secondes
- Navigation entre pages : 0.5-1 seconde
- Mise à jour de graphiques : < 500ms
- Simulation A/B : 1-2 secondes

## Dépannage

### Problème : Le dashboard ne démarre pas

Solution :

```bash
# Vérifier l'installation des dépendances
pip install -r requirements.txt --upgrade

# Vérifier les données
ls data/clean/
```

### Problème : Données non trouvées

Solution :

- Vérifier que les fichiers CSV sont dans `data/raw/`
- Exécuter le script de préparation si nécessaire
- Le dashboard génère des données de démo si fichiers absents

### Problème : Erreur JSON dans tests A/B

Solution :

- Le fichier `ab_test_results.json` peut être corrompu
- Supprimer le fichier, il sera recréé automatiquement
- Ou vérifier la structure JSON dans la section "Structure des données"

### Problème : Graphiques ne s'affichent pas

Solution :

- Vérifier la console JavaScript du navigateur (F12)
- Vider le cache du navigateur (Ctrl + Shift + Delete)
- Relancer le serveur Dash

### Problème : Performances lentes

Solution :

- Activer le cache Redis au lieu de simple
- Réduire la plage de dates sélectionnée
- Augmenter le timeout du cache
- Ajouter plus de workers Gunicorn en production

## Contribution

Pour contribuer au projet :

1. Créer une branche pour la fonctionnalité

```bash
git checkout -b feature/nouvelle-fonctionnalite
```

2. Commiter les changements

```bash
git commit -m "Ajout de [fonctionnalité]"
```

3. Pousser vers la branche

```bash
git push origin feature/nouvelle-fonctionnalite
```

4. Créer une Pull Request

## Tests

Lancer les tests unitaires :

```bash
pytest test_dashboard_integration.py -v
```

Avec couverture de code :

```bash
pytest --cov=dashboard_app --cov-report=html
```

## Licence

Ce projet est développé à des fins éducatives et d'analyse de données e-commerce.

## Support

Pour toute question ou problème :

1. Vérifier la section Dépannage ci-dessus
2. Consulter les logs du serveur dans le terminal
3. Vérifier la console JavaScript du navigateur
4. S'assurer que toutes les dépendances sont installées

## Roadmap

Fonctionnalités futures envisagées :

- Connexion à bases de données en temps réel (PostgreSQL, MongoDB)
- Export des rapports en PDF
- Alertes automatiques sur métriques critiques
- Prédictions de ventes avec Machine Learning
- Analyse de sentiment sur reviews produits
- Recommandations produits personnalisées
- API REST pour intégration externe
- Multi-utilisateurs avec authentification
- Tableaux de bord personnalisables par utilisateur
- Support multilingue

## Changelog

### Version 2.0.0 (2026-01-29)

- Migration vers thème sombre (DARKLY)
- Ajout sidebar navigation + header fixe
- Implémentation simulateur tests A/B intégré
- Remplacement tableau produits par treemap
- Suppression de tous les emojis/icônes
- Ajout de 15+ nouvelles visualisations
- Optimisation des filtres de dates (données réelles)
- Correction bugs de chargement KPIs
- Amélioration performances avec cache
- Application cohérente du thème plotly_dark

### Version 1.0.0 (2026-01-15)

- Version initiale du dashboard
- 6 pages d'analyse
- Visualisations de base
- Thème clair Bootstrap

## Auteurs

Projet développé dans le cadre d'une analyse de données e-commerce avec focus sur la visualisation interactive et l'optimisation de la conversion.

## Remerciements

- Dataset basé sur RetailRocket e-commerce data
- Framework Dash par Plotly
- Bootstrap pour le design système
- Communauté Python pour les bibliothèques open-source
# ecommerce-per
