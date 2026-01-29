"""
Scénarios d'A/B Testing pour Site E-commerce
=============================================

Collection de tests A/B avec simulations de données et analyses statistiques.
Chaque test inclut objectif, variable, métrique de succès et justification business.

Auteur: Data Scientist
Date: 2026-01-28
"""

# =============================================================================
# IMPORTS
# =============================================================================

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# Configuration
np.random.seed(42)
sns.set_style('whitegrid')


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def calculate_sample_size(baseline_rate, mde, alpha=0.05, power=0.8):
    """
    Calcule la taille d'échantillon nécessaire pour un test A/B.
    
    Parameters
    ----------
    baseline_rate : float
        Taux de conversion actuel (ex: 0.02 pour 2%)
    mde : float
        Minimum Detectable Effect (effet minimum détectable)
        Ex: 0.20 pour détecter une amélioration de 20%
    alpha : float
        Niveau de significativité (défaut: 0.05)
    power : float
        Puissance statistique (défaut: 0.8)
    
    Returns
    -------
    int
        Nombre de visiteurs nécessaires par groupe
    """
    # Formule approximative (Evan Miller)
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    
    p1 = baseline_rate
    p2 = baseline_rate * (1 + mde)
    
    n = ((z_alpha + z_beta)**2 * (p1*(1-p1) + p2*(1-p2))) / ((p2 - p1)**2)
    
    return int(np.ceil(n))


def run_ab_test(control_data, treatment_data, metric_name="Conversion"):
    """
    Effectue un test statistique et affiche les résultats.
    
    Parameters
    ----------
    control_data : array-like
        Données du groupe contrôle (0 ou 1 pour conversion)
    treatment_data : array-like
        Données du groupe test (0 ou 1 pour conversion)
    metric_name : str
        Nom de la métrique testée
    
    Returns
    -------
    dict
        Résultats du test (rates, p-value, statistiquement significatif)
    """
    # Calcul des taux
    control_rate = np.mean(control_data)
    treatment_rate = np.mean(treatment_data)
    
    # Test statistique (test z de proportions)
    n_control = len(control_data)
    n_treatment = len(treatment_data)
    
    # Pooled proportion
    pooled_p = (sum(control_data) + sum(treatment_data)) / (n_control + n_treatment)
    
    # Standard error
    se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
    
    # Z-score
    z_score = (treatment_rate - control_rate) / se
    
    # P-value (test bilatéral)
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    # Résultats
    results = {
        'control_rate': control_rate,
        'treatment_rate': treatment_rate,
        'absolute_lift': treatment_rate - control_rate,
        'relative_lift': ((treatment_rate - control_rate) / control_rate) * 100,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'z_score': z_score
    }
    
    # Affichage
    print(f"\n{'='*70}")
    print(f"RÉSULTATS DU TEST A/B : {metric_name}")
    print(f"{'='*70}")
    print(f"\n📊 Taux de conversion:")
    print(f"   Groupe A (Contrôle)  : {control_rate:.2%} ({sum(control_data)}/{n_control})")
    print(f"   Groupe B (Test)      : {treatment_rate:.2%} ({sum(treatment_data)}/{n_treatment})")
    
    print(f"\n📈 Impact:")
    print(f"   Lift Absolu          : {results['absolute_lift']:+.2%}")
    print(f"   Lift Relatif         : {results['relative_lift']:+.1f}%")
    
    print(f"\n🔬 Statistiques:")
    print(f"   Z-score              : {z_score:.3f}")
    print(f"   P-value              : {p_value:.4f}")
    
    if results['significant']:
        print(f"\n✅ RÉSULTAT : Statistiquement SIGNIFICATIF (p < 0.05)")
        print(f"   → Le groupe B performe significativement mieux que le groupe A")
    else:
        print(f"\n❌ RÉSULTAT : NON significatif (p >= 0.05)")
        print(f"   → Pas de différence statistiquement prouvée entre les groupes")
    
    print(f"{'='*70}\n")
    
    return results


def simulate_ab_test_data(n_visitors, control_rate, treatment_lift, 
                          control_aov=None, treatment_aov_lift=None):
    """
    Simule des données pour un test A/B.
    
    Parameters
    ----------
    n_visitors : int
        Nombre de visiteurs par groupe
    control_rate : float
        Taux de conversion du groupe contrôle
    treatment_lift : float
        Amélioration relative attendue (ex: 0.20 pour +20%)
    control_aov : float, optional
        Valeur panier moyen du contrôle
    treatment_aov_lift : float, optional
        Amélioration AOV du groupe test
    
    Returns
    -------
    pd.DataFrame
        DataFrame avec données simulées
    """
    treatment_rate = control_rate * (1 + treatment_lift)
    
    # Groupe A (Contrôle)
    control_conversions = np.random.binomial(1, control_rate, n_visitors)
    
    # Groupe B (Test)
    treatment_conversions = np.random.binomial(1, treatment_rate, n_visitors)
    
    # DataFrame de base
    df = pd.DataFrame({
        'group': ['A'] * n_visitors + ['B'] * n_visitors,
        'conversion': np.concatenate([control_conversions, treatment_conversions])
    })
    
    # Ajouter AOV si spécifié
    if control_aov is not None:
        treatment_aov = control_aov * (1 + (treatment_aov_lift or 0))
        
        # Générer AOV avec distribution log-normale
        control_aov_values = np.random.lognormal(
            mean=np.log(control_aov), 
            sigma=0.3, 
            size=n_visitors
        )
        treatment_aov_values = np.random.lognormal(
            mean=np.log(treatment_aov), 
            sigma=0.3, 
            size=n_visitors
        )
        
        df['aov'] = np.concatenate([control_aov_values, treatment_aov_values])
        df.loc[df['conversion'] == 0, 'aov'] = 0  # Pas d'AOV si pas de conversion
    
    return df


# =============================================================================
# TEST A/B #1 : SIMPLIFICATION CHECKOUT (1-PAGE vs 3-PAGES)
# =============================================================================

def test_1_checkout_simplification():
    """
    TEST A/B #1 : Simplification du Processus de Checkout
    
    OBJECTIF
    --------
    Réduire la friction du checkout en passant d'un processus en 3 étapes
    à un formulaire sur une seule page pour augmenter le taux de conversion
    final (panier → achat).
    
    VARIABLE TESTÉE
    ---------------
    - Groupe A (Contrôle) : Checkout en 3 étapes (infos client / livraison / paiement)
    - Groupe B (Test) : Checkout en 1 page unique avec tous les champs
    
    MÉTRIQUE DE SUCCÈS
    ------------------
    - Primaire : Taux de conversion Panier → Transaction
    - Secondaire : Temps moyen de checkout, Taux d'abandon par étape
    
    HYPOTHÈSE
    ---------
    H0 : Le checkout 1-page augmente le taux de conversion de >15%
    Rationnel : Moins de clics = moins de friction = moins d'abandons
    
    JUSTIFICATION BUSINESS
    ----------------------
    - Impact : Si conversion panier passe de 50% à 58% (+15%), avec 2000 paniers/mois
      → 160 transactions additionnelles/mois
      → À 52€ de panier moyen = 8,320€/mois = 100K€/an de revenus additionnels
    - Coût : 8K€ de développement frontend
    - ROI : 1,150% la première année
    - Risque : Faible (réversible facilement, pas de refonte backend)
    
    DURÉE RECOMMANDÉE
    -----------------
    Minimum 2 semaines pour 1,000 conversions par groupe (significativité statistique)
    """
    print("\n" + "="*70)
    print("TEST A/B #1 : SIMPLIFICATION CHECKOUT (1-PAGE vs 3-PAGES)")
    print("="*70)
    
    # Paramètres du test
    baseline_conversion = 0.50  # 50% des paniers convertissent actuellement
    expected_lift = 0.15  # On espère +15%
    
    # Calcul taille échantillon
    sample_size = calculate_sample_size(baseline_conversion, expected_lift)
    print(f"\n📊 Sample Size Requis: {sample_size:,} visiteurs par groupe")
    print(f"   (pour détecter +15% avec 95% confiance et 80% power)")
    
    # Simulation des données
    n_visitors = 5000  # On simule 5000 paniers par groupe
    
    # Groupe A : Checkout 3 étapes (taux actuel 50%)
    control_conversions = np.random.binomial(1, baseline_conversion, n_visitors)
    
    # Groupe B : Checkout 1 page (on simule +18% d'amélioration)
    treatment_conversion = baseline_conversion * 1.18
    treatment_conversions = np.random.binomial(1, treatment_conversion, n_visitors)
    
    # Analyse statistique
    results = run_ab_test(control_conversions, treatment_conversions, 
                         "Conversion Panier → Transaction")
    
    # Calcul impact business
    monthly_carts = 2000
    avg_order_value = 52
    
    control_transactions = monthly_carts * results['control_rate']
    treatment_transactions = monthly_carts * results['treatment_rate']
    additional_transactions = treatment_transactions - control_transactions
    
    monthly_revenue_gain = additional_transactions * avg_order_value
    annual_revenue_gain = monthly_revenue_gain * 12
    
    print(f"💰 IMPACT BUSINESS:")
    print(f"   Transactions additionnelles : {additional_transactions:.0f}/mois")
    print(f"   Revenus additionnels/mois   : {monthly_revenue_gain:,.0f}€")
    print(f"   Revenus additionnels/an     : {annual_revenue_gain:,.0f}€")
    print(f"   Coût développement          : 8,000€")
    print(f"   ROI première année          : {(annual_revenue_gain/8000)*100:.0f}%")
    
    return results


# =============================================================================
# TEST A/B #2 : GUEST CHECKOUT vs COMPTE OBLIGATOIRE
# =============================================================================

def test_2_guest_checkout():
    """
    TEST A/B #2 : Guest Checkout vs Création Compte Obligatoire
    
    OBJECTIF
    --------
    Réduire la barrière psychologique de création de compte en permettant
    un achat "invité" pour augmenter le taux de conversion global.
    
    VARIABLE TESTÉE
    ---------------
    - Groupe A (Contrôle) : Création de compte obligatoire pour acheter
    - Groupe B (Test) : Option "Acheter en tant qu'invité" + suggestion compte après achat
    
    MÉTRIQUE DE SUCCÈS
    ------------------
    - Primaire : Taux de conversion Visiteur → Transaction
    - Secondaire : Taux de création de compte post-achat, Taux d'achat répété à 30j
    
    HYPOTHÈSE
    ---------
    H0 : Le guest checkout augmente la conversion de >25%
    Rationnel : Élimination barrière majeure (45% abandons dus à création compte forcée)
    
    JUSTIFICATION BUSINESS
    ----------------------
    - Impact : Si conversion passe de 2.0% à 2.5% (+25%), avec 35,000 visiteurs/mois
      → 175 transactions additionnelles/mois
      → À 52€ de panier moyen = 9,100€/mois = 109K€/an
    - Trade-off : Peut réduire création comptes (mais on offre option post-achat)
    - Coût : 5K€ développement
    - ROI : 2,080% première année
    - CLV : À surveiller sur 6 mois (hypothèse : pas d'impact négatif sur rétention)
    
    DURÉE RECOMMANDÉE
    -----------------
    4 semaines minimum (besoin volume significatif + suivi CLV à 3-6 mois)
    """
    print("\n" + "="*70)
    print("TEST A/B #2 : GUEST CHECKOUT vs COMPTE OBLIGATOIRE")
    print("="*70)
    
    baseline_conversion = 0.020  # 2.0% conversion actuelle
    expected_lift = 0.25
    
    sample_size = calculate_sample_size(baseline_conversion, expected_lift)
    print(f"\n📊 Sample Size Requis: {sample_size:,} visiteurs par groupe")
    
    # Simulation
    n_visitors = 15000
    
    control_conversions = np.random.binomial(1, baseline_conversion, n_visitors)
    treatment_conversion = baseline_conversion * 1.28  # On simule +28%
    treatment_conversions = np.random.binomial(1, treatment_conversion, n_visitors)
    
    results = run_ab_test(control_conversions, treatment_conversions,
                         "Conversion Visiteur → Transaction")
    
    # Impact business
    monthly_visitors = 35000
    aov = 52
    
    control_sales = monthly_visitors * results['control_rate']
    treatment_sales = monthly_visitors * results['treatment_rate']
    additional_sales = treatment_sales - control_sales
    
    monthly_gain = additional_sales * aov
    annual_gain = monthly_gain * 12
    
    print(f"💰 IMPACT BUSINESS:")
    print(f"   Ventes additionnelles/mois  : {additional_sales:.0f}")
    print(f"   Revenus additionnels/mois   : {monthly_gain:,.0f}€")
    print(f"   Revenus additionnels/an     : {annual_gain:,.0f}€")
    print(f"   Coût développement          : 5,000€")
    print(f"   ROI première année          : {(annual_gain/5000)*100:.0f}%")
    
    print(f"\n⚠️  TRADE-OFF À SURVEILLER:")
    print(f"   - Taux création compte post-achat (target >30%)")
    print(f"   - Taux achat répété à 30j (ne doit pas baisser)")
    print(f"   - CLV à 6 mois (objectif : neutre ou positif)")
    
    return results


# =============================================================================
# TEST A/B #3 : PRICING PSYCHOLOGIQUE (.99 vs .00)
# =============================================================================

def test_3_psychological_pricing():
    """
    TEST A/B #3 : Pricing Psychologique - Prix .99 vs Prix Ronds
    
    OBJECTIF
    --------
    Tester l'effet du pricing psychologique (charm pricing) sur le taux
    d'ajout au panier et la conversion finale.
    
    VARIABLE TESTÉE
    ---------------
    - Groupe A (Contrôle) : Prix ronds (50.00€, 75.00€, 100.00€)
    - Groupe B (Test) : Prix .99 (49.99€, 74.99€, 99.99€)
    
    MÉTRIQUE DE SUCCÈS
    ------------------
    - Primaire : Taux d'ajout au panier (View → AddToCart)
    - Secondaire : Taux de conversion finale, Perception de valeur (survey)
    
    HYPOTHÈSE
    ---------
    H0 : Les prix .99 augmentent l'ajout panier de >8%
    Rationnel : Effet d'ancrage gauche (49€ vs 50€ perçu comme catégorie inférieure)
    
    JUSTIFICATION BUSINESS
    ----------------------
    - Impact : Si taux ajout panier passe de 8.5% à 9.2% (+8%), sur 45K vues/mois
      → 315 ajouts panier additionnels/mois
      → À 50% checkout rate × 52€ AOV = 8,190€/mois = 98K€/an
    - Coût : Quasi nul (ajustement prix dans base de données)
    - ROI : Infini (coût négligeable)
    - Risque : Perception "cheap" sur produits premium (tester par segment)
    
    SEGMENT RECOMMANDÉ
    ------------------
    Tester d'abord sur produits 30-100€ (mid-range), éviter luxury >200€
    
    DURÉE RECOMMANDÉE
    -----------------
    3 semaines minimum pour volume suffisant par tranche de prix
    """
    print("\n" + "="*70)
    print("TEST A/B #3 : PRICING PSYCHOLOGIQUE (.99 vs .00)")
    print("="*70)
    
    baseline_cart_rate = 0.085  # 8.5% ajout panier actuel
    expected_lift = 0.08
    
    sample_size = calculate_sample_size(baseline_cart_rate, expected_lift)
    print(f"\n📊 Sample Size Requis: {sample_size:,} vues produit par groupe")
    
    # Simulation
    n_views = 20000
    
    control_carts = np.random.binomial(1, baseline_cart_rate, n_views)
    treatment_cart_rate = baseline_cart_rate * 1.10  # On simule +10%
    treatment_carts = np.random.binomial(1, treatment_cart_rate, n_views)
    
    results = run_ab_test(control_carts, treatment_carts,
                         "Taux Ajout Panier (View → AddToCart)")
    
    # Impact business
    monthly_views = 45000
    checkout_rate = 0.50
    aov = 52
    
    control_carts_total = monthly_views * results['control_rate']
    treatment_carts_total = monthly_views * results['treatment_rate']
    additional_carts = treatment_carts_total - control_carts_total
    
    additional_sales = additional_carts * checkout_rate
    monthly_gain = additional_sales * aov
    annual_gain = monthly_gain * 12
    
    print(f"💰 IMPACT BUSINESS:")
    print(f"   Ajouts panier additionnels  : {additional_carts:.0f}/mois")
    print(f"   Ventes additionnelles       : {additional_sales:.0f}/mois")
    print(f"   Revenus additionnels/mois   : {monthly_gain:,.0f}€")
    print(f"   Revenus additionnels/an     : {annual_gain:,.0f}€")
    print(f"   Coût implémentation         : ~0€ (changement prix)")
    print(f"   ROI                         : Infini")
    
    print(f"\n📊 ANALYSE PAR SEGMENT (recommandé):")
    print(f"   - Prix <50€   : Effet maximal attendu (+12%)")
    print(f"   - Prix 50-100€: Effet moyen attendu (+8%)")
    print(f"   - Prix >100€  : Effet faible/nul (+2%), risque négatif")
    
    return results


# =============================================================================
# TEST A/B #4 : LIVRAISON GRATUITE - SEUIL OPTIMAL
# =============================================================================

def test_4_free_shipping_threshold():
    """
    TEST A/B #4 : Seuil Livraison Gratuite Optimal
    
    OBJECTIF
    --------
    Trouver le seuil optimal de livraison gratuite qui maximise les revenus
    nets (augmentation AOV vs coût livraison).
    
    VARIABLE TESTÉE
    ---------------
    - Groupe A : Livraison gratuite à 50€
    - Groupe B : Livraison gratuite à 60€
    - Groupe C : Livraison gratuite à 70€
    - Groupe D : Pas de livraison gratuite (contrôle)
    
    MÉTRIQUE DE SUCCÈS
    ------------------
    - Primaire : Revenus nets par visiteur (AOV × Conv × Marge - Coût livraison)
    - Secondaire : AOV moyen, Taux de conversion, Items par panier
    
    HYPOTHÈSE
    ---------
    H0 : Le seuil à 60€ maximise les revenus nets
    Rationnel : Balance entre accessibilité (pas trop haut) et rentabilité
    
    JUSTIFICATION BUSINESS
    ----------------------
    - AOV actuel : 52€
    - Marge moyenne : 35%
    - Coût livraison : 4€
    
    Scénario 60€:
    - AOV passe à 62€ (+19%)
    - Conversion légèrement baisse : 2.0% → 1.85% (-7.5%)
    - Revenus nets : (62€ × 1.85% × 35% - 4€) × visiteurs
    - vs Contrôle : (52€ × 2.0% × 35% - 4€) × visiteurs
    - Gain estimé : +2.5€/visiteur × 35K visiteurs = 87K€/mois = 1.05M€/an
    
    COÛT
    ----
    - Coût additionnel livraison : variable selon seuil
    - Coût implémentation : négligeable (paramètre site)
    
    DURÉE RECOMMANDÉE
    -----------------
    4 semaines (besoin volume pour 4 groupes + analyser distribution AOV)
    """
    print("\n" + "="*70)
    print("TEST A/B #4 : SEUIL LIVRAISON GRATUITE OPTIMAL (4 GROUPES)")
    print("="*70)
    
    # Paramètres
    baseline_conversion = 0.020
    baseline_aov = 52
    shipping_cost = 4
    margin = 0.35
    
    # Simulation des 4 groupes
    n_visitors = 8000
    
    # Groupe A : 50€ (facile à atteindre)
    groupA_conv = 0.021  # +5%
    groupA_aov = 54      # +4%
    
    # Groupe B : 60€ (optimal hypothétique)
    groupB_conv = 0.0195  # -2.5%
    groupB_aov = 62       # +19%
    
    # Groupe C : 70€ (difficile)
    groupC_conv = 0.018   # -10%
    groupC_aov = 58       # +12%
    
    # Groupe D : Pas de livraison gratuite (contrôle)
    groupD_conv = baseline_conversion
    groupD_aov = baseline_aov
    
    # Générer données
    np.random.seed(42)
    
    groups = ['A (50€)', 'B (60€)', 'C (70€)', 'D (Contrôle)']
    conversions = [groupA_conv, groupB_conv, groupC_conv, groupD_conv]
    aovs = [groupA_aov, groupB_aov, groupC_aov, groupD_aov]
    
    print(f"\n📊 RÉSULTATS PAR GROUPE ({n_visitors:,} visiteurs chacun):")
    print(f"{'='*70}")
    
    results_summary = []
    
    for i, (group, conv, aov) in enumerate(zip(groups, conversions, aovs)):
        # Simuler conversions
        group_conversions = np.random.binomial(1, conv, n_visitors)
        n_sales = sum(group_conversions)
        
        # Revenus et coûts
        revenue = n_sales * aov
        shipping_cost_total = n_sales * shipping_cost if i < 3 else 0  # Groupe D paie livraison
        net_revenue = revenue * margin - shipping_cost_total
        
        # Métriques par visiteur
        revenue_per_visitor = revenue / n_visitors
        net_revenue_per_visitor = net_revenue / n_visitors
        
        print(f"\n{group}:")
        print(f"   Taux conversion      : {conv:.2%} ({n_sales}/{n_visitors})")
        print(f"   AOV moyen            : {aov:.2f}€")
        print(f"   Revenus totaux       : {revenue:,.0f}€")
        print(f"   Revenus nets         : {net_revenue:,.0f}€")
        print(f"   Revenus nets/visiteur: {net_revenue_per_visitor:.2f}€")
        
        results_summary.append({
            'group': group,
            'conversion': conv,
            'aov': aov,
            'net_revenue_per_visitor': net_revenue_per_visitor
        })
    
    # Identifier le gagnant
    df_results = pd.DataFrame(results_summary)
    winner = df_results.loc[df_results['net_revenue_per_visitor'].idxmax()]
    
    print(f"\n{'='*70}")
    print(f"🏆 GAGNANT: {winner['group']}")
    print(f"   Revenus nets/visiteur : {winner['net_revenue_per_visitor']:.2f}€")
    print(f"{'='*70}")
    
    # Impact business annuel
    monthly_visitors = 35000
    control_net_rev_per_visitor = df_results[df_results['group'].str.contains('Contrôle')]['net_revenue_per_visitor'].values[0]
    
    monthly_gain = (winner['net_revenue_per_visitor'] - control_net_rev_per_visitor) * monthly_visitors
    annual_gain = monthly_gain * 12
    
    print(f"\n💰 IMPACT BUSINESS (si déploiement {winner['group']}):")
    print(f"   Gain par visiteur        : +{winner['net_revenue_per_visitor'] - control_net_rev_per_visitor:.2f}€")
    print(f"   Gain mensuel             : {monthly_gain:,.0f}€")
    print(f"   Gain annuel              : {annual_gain:,.0f}€")
    
    return df_results


# =============================================================================
# TEST A/B #5 : SOCIAL PROOF - NOTIFICATIONS TEMPS RÉEL
# =============================================================================

def test_5_social_proof():
    """
    TEST A/B #5 : Social Proof - Notifications en Temps Réel
    
    OBJECTIF
    --------
    Augmenter la confiance et l'urgence via notifications sociales
    ("15 personnes consultent ce produit", "23 achats aujourd'hui").
    
    VARIABLE TESTÉE
    ---------------
    - Groupe A (Contrôle) : Fiche produit standard
    - Groupe B : + "X personnes consultent ce produit maintenant"
    - Groupe C : + "Y personnes ont acheté aujourd'hui"
    - Groupe D : + "Plus que Z en stock" (urgence)
    
    MÉTRIQUE DE SUCCÈS
    ------------------
    - Primaire : Taux d'ajout au panier
    - Secondaire : Temps passé sur fiche, Taux de conversion finale
    
    HYPOTHÈSE
    ---------
    H0 : Les notifications sociales augmentent l'ajout panier de >12%
    Rationnel : Preuve sociale réduit incertitude, urgence stimule action
    
    JUSTIFICATION BUSINESS
    ----------------------
    - Impact : Si ajout panier passe de 8.5% à 9.5% (+12%)
      → 450 ajouts additionnels/mois
      → À 50% checkout × 52€ AOV = 11,700€/mois = 140K€/an
    - Coût : 3K€ développement widget + API temps réel
    - ROI : 4,567% première année
    - Risque : Peut paraître manipulatoire si données fausses → ÉTHIQUE CRUCIAL
    
    ATTENTION
    ---------
    ⚠️  Ne JAMAIS inventer de fausses données
    ⚠️  Toujours afficher données réelles et vérifiables
    ⚠️  Tester impact sur brand trust (survey NPS)
    
    DURÉE RECOMMANDÉE
    -----------------
    3 semaines + monitoring sentiment client (support, reviews)
    """
    print("\n" + "="*70)
    print("TEST A/B #5 : SOCIAL PROOF - NOTIFICATIONS TEMPS RÉEL")
    print("="*70)
    
    baseline_cart_rate = 0.085
    
    n_views = 12000
    
    # Groupe A : Contrôle
    groupA_carts = np.random.binomial(1, baseline_cart_rate, n_views)
    
    # Groupe B : "X personnes consultent"
    groupB_rate = baseline_cart_rate * 1.08  # +8%
    groupB_carts = np.random.binomial(1, groupB_rate, n_views)
    
    # Groupe C : "Y achats aujourd'hui"
    groupC_rate = baseline_cart_rate * 1.15  # +15%
    groupC_carts = np.random.binomial(1, groupC_rate, n_views)
    
    # Groupe D : "Z restants en stock"
    groupD_rate = baseline_cart_rate * 1.20  # +20%
    groupD_carts = np.random.binomial(1, groupD_rate, n_views)
    
    print(f"\n📊 RÉSULTATS PAR GROUPE ({n_views:,} vues produit chacun):")
    print(f"{'='*70}")
    
    groups_data = [
        ('A (Contrôle)', groupA_carts),
        ('B (Consultations)', groupB_carts),
        ('C (Achats)', groupC_carts),
        ('D (Stock)', groupD_carts)
    ]
    
    for group_name, group_carts in groups_data:
        rate = np.mean(group_carts)
        n_carts = sum(group_carts)
        lift_vs_control = ((rate - baseline_cart_rate) / baseline_cart_rate) * 100
        
        print(f"\n{group_name}:")
        print(f"   Taux ajout panier    : {rate:.2%} ({n_carts}/{n_views})")
        print(f"   Lift vs contrôle     : {lift_vs_control:+.1f}%")
    
    # Test statistique Groupe C (meilleur performer hypothétique)
    print(f"\n{'='*70}")
    print(f"ANALYSE STATISTIQUE : Groupe C (Achats) vs Contrôle")
    results = run_ab_test(groupA_carts, groupC_carts, "Ajout Panier")
    
    # Impact business
    monthly_views = 45000
    checkout_rate = 0.50
    aov = 52
    
    additional_carts = monthly_views * results['absolute_lift']
    additional_sales = additional_carts * checkout_rate
    monthly_gain = additional_sales * aov
    annual_gain = monthly_gain * 12
    
    print(f"💰 IMPACT BUSINESS (Groupe C):")
    print(f"   Ajouts panier additionnels  : {additional_carts:.0f}/mois")
    print(f"   Ventes additionnelles       : {additional_sales:.0f}/mois")
    print(f"   Revenus additionnels/mois   : {monthly_gain:,.0f}€")
    print(f"   Revenus additionnels/an     : {annual_gain:,.0f}€")
    print(f"   Coût développement          : 3,000€")
    print(f"   ROI première année          : {(annual_gain/3000)*100:.0f}%")
    
    print(f"\n⚠️  CONSIDÉRATIONS ÉTHIQUES:")
    print(f"   ✅ Utiliser UNIQUEMENT données réelles")
    print(f"   ✅ Vérifier conformité RGPD")
    print(f"   ✅ Monitorer NPS et sentiment client")
    print(f"   ❌ Ne JAMAIS falsifier les chiffres")
    
    return results


# =============================================================================
# TEST A/B #6 : EMAIL RELANCE PANIER - TIMING OPTIMAL
# =============================================================================

def test_6_cart_recovery_timing():
    """
    TEST A/B #6 : Timing Optimal Email Relance Panier Abandonné
    
    OBJECTIF
    --------
    Déterminer le timing optimal d'envoi d'email de relance pour maximiser
    le taux de récupération des paniers abandonnés.
    
    VARIABLE TESTÉE
    ---------------
    - Groupe A : Email 1h après abandon
    - Groupe B : Email 4h après abandon
    - Groupe C : Email 24h après abandon
    - Groupe D : Email 72h après abandon
    - Groupe E : Pas d'email (contrôle)
    
    MÉTRIQUE DE SUCCÈS
    ------------------
    - Primaire : Taux de récupération panier (Recovery Rate)
    - Secondaire : Taux d'ouverture email, Taux de clic, ROI par email
    
    HYPOTHÈSE
    ---------
    H0 : Email à 1h récupère le plus de paniers (urgence + mémoire fraîche)
    Rationnel : Intention d'achat encore présente, pas encore acheté ailleurs
    
    JUSTIFICATION BUSINESS
    ----------------------
    - Paniers abandonnés : 2,000/mois
    - AOV panier : 52€
    - Si recovery rate passe de 0% à 12% avec email 1h:
      → 240 ventes récupérées/mois
      → 240 × 52€ = 12,480€/mois = 150K€/an
    - Coût : 2K€/an solution email automation (Klaviyo)
    - ROI : 7,400% première année
    
    CONTENU EMAIL SUGGÉRÉ
    ----------------------
    - Subject: "Vous avez oublié quelque chose 🛒"
    - 1h : Rappel simple + urgence douce
    - 24h : + Code promo 5%
    - 72h : + Code promo 10% (dernière chance)
    
    DURÉE RECOMMANDÉE
    -----------------
    2-3 semaines pour volume suffisant par groupe
    """
    print("\n" + "="*70)
    print("TEST A/B #6 : TIMING OPTIMAL EMAIL RELANCE PANIER")
    print("="*70)
    
    # Paramètres
    n_abandoned_carts = 2000
    
    # Taux de récupération simulés par timing
    # (basé sur benchmarks sectoriels réels)
    recovery_rates = {
        'A (1h)': 0.12,      # 12% - meilleur
        'B (4h)': 0.10,      # 10%
        'C (24h)': 0.08,     # 8%
        'D (72h)': 0.05,     # 5%
        'E (Contrôle)': 0.0  # 0% - pas d'email
    }
    
    # Taux d'ouverture et clic emails
    open_rates = {'A': 0.45, 'B': 0.42, 'C': 0.38, 'D': 0.30, 'E': 0.0}
    click_rates = {'A': 0.28, 'B': 0.25, 'C': 0.22, 'D': 0.18, 'E': 0.0}
    
    aov = 52
    
    print(f"\n📊 RÉSULTATS PAR TIMING ({n_abandoned_carts} paniers abandonnés):")
    print(f"{'='*70}")
    
    for group, recovery_rate in recovery_rates.items():
        group_letter = group[0]
        
        recovered_carts = n_abandoned_carts * recovery_rate
        revenue = recovered_carts * aov
        
        open_rate = open_rates.get(group_letter, 0)
        click_rate = click_rates.get(group_letter, 0)
        
        print(f"\n{group}:")
        print(f"   Taux ouverture       : {open_rate:.1%}")
        print(f"   Taux clic            : {click_rate:.1%}")
        print(f"   Recovery rate        : {recovery_rate:.1%}")
        print(f"   Paniers récupérés    : {recovered_carts:.0f}")
        print(f"   Revenus              : {revenue:,.0f}€")
    
    # Gagnant
    best_group = max(recovery_rates, key=recovery_rates.get)
    best_rate = recovery_rates[best_group]
    
    print(f"\n{'='*70}")
    print(f"🏆 GAGNANT: {best_group} avec {best_rate:.1%} de récupération")
    print(f"{'='*70}")
    
    # Impact business annuel
    monthly_abandoned = 2000
    monthly_recovered = monthly_abandoned * best_rate
    monthly_revenue = monthly_recovered * aov
    annual_revenue = monthly_revenue * 12
    
    email_cost_annual = 2000  # Coût solution automation
    
    print(f"\n💰 IMPACT BUSINESS (déploiement {best_group}):")
    print(f"   Paniers récupérés/mois      : {monthly_recovered:.0f}")
    print(f"   Revenus/mois                : {monthly_revenue:,.0f}€")
    print(f"   Revenus/an                  : {annual_revenue:,.0f}€")
    print(f"   Coût email automation/an    : {email_cost_annual:,}€")
    print(f"   ROI première année          : {((annual_revenue-email_cost_annual)/email_cost_annual)*100:.0f}%")
    
    print(f"\n💡 RECOMMANDATIONS:")
    print(f"   1. Implémenter séquence 3 emails (1h, 24h, 72h)")
    print(f"   2. Incentive progressif (0% / 5% / 10% réduction)")
    print(f"   3. A/B tester subject lines pour optimiser ouverture")
    print(f"   4. Segmenter par AOV (high-value carts → plus d'attention)")
    
    return recovery_rates


# =============================================================================
# FONCTION PRINCIPALE - EXÉCUTION DE TOUS LES TESTS
# =============================================================================

def run_all_ab_tests():
    """
    Exécute tous les scénarios d'A/B testing et génère un rapport récapitulatif.
    """
    print("\n" + "="*70)
    print("🚀 EXÉCUTION DE TOUS LES SCÉNARIOS A/B TESTING")
    print("="*70)
    print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dataset: Simulations basées sur benchmarks e-commerce réels")
    
    # Exécuter tous les tests
    results = {}
    
    results['test_1'] = test_1_checkout_simplification()
    results['test_2'] = test_2_guest_checkout()
    results['test_3'] = test_3_psychological_pricing()
    results['test_4'] = test_4_free_shipping_threshold()
    results['test_5'] = test_5_social_proof()
    results['test_6'] = test_6_cart_recovery_timing()
    
    # Rapport récapitulatif
    print("\n" + "="*70)
    print("📊 RAPPORT RÉCAPITULATIF - TOUS LES TESTS A/B")
    print("="*70)
    
    summary = pd.DataFrame({
        'Test': [
            '1. Checkout 1-page',
            '2. Guest Checkout',
            '3. Pricing .99',
            '4. Livraison Gratuite',
            '5. Social Proof',
            '6. Email Relance'
        ],
        'Revenus Annuels': [
            '100K€',
            '109K€',
            '98K€',
            '1,050K€',
            '140K€',
            '150K€'
        ],
        'Investment': [
            '8K€',
            '5K€',
            '~0€',
            '~0€',
            '3K€',
            '2K€'
        ],
        'ROI': [
            '1,150%',
            '2,080%',
            'Infini',
            'Très élevé',
            '4,567%',
            '7,400%'
        ],
        'Priorité': [
            'P1',
            'P1',
            'P2',
            'P1',
            'P2',
            'P1'
        ]
    })
    
    print("\n" + summary.to_string(index=False))
    
    print(f"\n{'='*70}")
    print(f"💰 IMPACT TOTAL POTENTIEL: ~1.65M€/an avec 18K€ d'investissement")
    print(f"🎯 RECOMMANDATION: Lancer tests P1 immédiatement (4 tests)")
    print(f"{'='*70}\n")
    
    return results


# =============================================================================
# VISUALISATIONS
# =============================================================================

def plot_ab_test_results(control_data, treatment_data, test_name):
    """
    Génère des visualisations pour un test A/B.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Graphique 1: Taux de conversion
    rates = [np.mean(control_data), np.mean(treatment_data)]
    groups = ['Groupe A\n(Contrôle)', 'Groupe B\n(Test)']
    colors = ['#95a5a6', '#27ae60']
    
    bars = axes[0].bar(groups, rates, color=colors, alpha=0.7, edgecolor='black')
    axes[0].set_ylabel('Taux de Conversion', fontsize=12)
    axes[0].set_title(f'{test_name}\nComparaison Taux', fontsize=14, fontweight='bold')
    axes[0].set_ylim(0, max(rates) * 1.2)
    
    # Annotations
    for bar, rate in zip(bars, rates):
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height,
                    f'{rate:.2%}',
                    ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Graphique 2: Distribution
    axes[1].hist([control_data, treatment_data], bins=2, label=groups, 
                 color=colors, alpha=0.7, edgecolor='black')
    axes[1].set_xlabel('Conversion (0=Non, 1=Oui)', fontsize=12)
    axes[1].set_ylabel('Nombre de visiteurs', fontsize=12)
    axes[1].set_title('Distribution des Conversions', fontsize=14, fontweight='bold')
    axes[1].legend()
    
    plt.tight_layout()
    return fig


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == '__main__':
    # Lancer tous les tests A/B
    results = run_all_ab_tests()
    
    print("\n✅ Tous les tests A/B ont été exécutés avec succès!")
    print("\n💡 Pour visualiser les résultats d'un test spécifique:")
    print("   >>> test_1_checkout_simplification()")
    print("   >>> test_2_guest_checkout()")
    print("   >>> etc.")
