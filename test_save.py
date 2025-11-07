# Test du système de sauvegarde
import json
import os
from datetime import datetime
import shutil

# Variable globale pour désactiver auto-save pendant le chargement
_is_loading = False

def save_data(data, force_backup=False):
    """Sauvegarde ultra-sécurisée"""
    try:
        os.makedirs('data', exist_ok=True)

        # 1. Sauvegarde temporaire
        temp_file = 'data/economy_temp.json'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # 2. Backup du précédent
        if os.path.exists('data/economy.json'):
            shutil.copy2('data/economy.json', 'data/economy_old.json')
        shutil.move(temp_file, 'data/economy.json')

        print("[SAVE] Donnees sauvegardees avec succes!")
        return True
    except Exception as e:
        print(f"[ERROR] Erreur sauvegarde: {e}")
        return False

# Wrapper pour les profils utilisateurs
class UserProfile(dict):
    """Profil utilisateur avec sauvegarde automatique"""
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        global _is_loading
        if not _is_loading:
            try:
                save_data(economy_data)
                print(f"[AUTO-SAVE] {key} modifie -> Sauvegarde instantanee!")
            except Exception as e:
                print(f"[ERROR] Erreur auto-save: {e}")

# Charger les données
def load_data():
    global _is_loading
    _is_loading = True

    try:
        if os.path.exists('data/economy.json'):
            with open('data/economy.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convertir tous les profils en UserProfile
            print("[LOAD] Conversion des profils...")
            for guild_id in data:
                for user_id in data[guild_id]:
                    if not isinstance(data[guild_id][user_id], UserProfile):
                        data[guild_id][user_id] = UserProfile(data[guild_id][user_id])

            print(f"[LOAD] {sum(len(g) for g in data.values())} profils convertis")
            return data
        return {}
    finally:
        _is_loading = False

# TEST
print("=" * 50)
print("TEST DU SYSTEME DE SAUVEGARDE")
print("=" * 50)

# Charger les données
economy_data = load_data()
print(f"\n[TEST] Donnees chargees: {len(economy_data)} serveurs")

# Créer un profil de test
test_guild = "123456789"
test_user = "987654321"

if test_guild not in economy_data:
    economy_data[test_guild] = {}

if test_user not in economy_data[test_guild]:
    print("\n[TEST] Creation d'un nouveau profil utilisateur...")
    economy_data[test_guild][test_user] = UserProfile({
        "balance": 0,
        "total_earned": 0,
        "games_played": 0
    })

# TEST 1: Modifier le balance
print("\n[TEST 1] Modification du balance...")
profile = economy_data[test_guild][test_user]
profile['balance'] = 100
print(f"[TEST 1] Balance apres modification: {profile['balance']}")

# TEST 2: Ajouter au balance
print("\n[TEST 2] Ajout au balance avec +=...")
profile['balance'] += 50
print(f"[TEST 2] Balance apres ajout: {profile['balance']}")

# TEST 3: Modifier plusieurs champs
print("\n[TEST 3] Modification de plusieurs champs...")
profile['total_earned'] = 150
profile['games_played'] = 5

# Vérifier que les données sont bien sauvegardées
print("\n[TEST 4] Verification de la sauvegarde...")
with open('data/economy.json', 'r', encoding='utf-8') as f:
    saved_data = json.load(f)

if test_guild in saved_data and test_user in saved_data[test_guild]:
    saved_profile = saved_data[test_guild][test_user]
    print(f"[TEST 4] Balance sauvegarde: {saved_profile['balance']}")
    print(f"[TEST 4] Total earned sauvegarde: {saved_profile['total_earned']}")
    print(f"[TEST 4] Games played sauvegarde: {saved_profile['games_played']}")

    if saved_profile['balance'] == 150 and saved_profile['total_earned'] == 150:
        print("\n[SUCCESS] Toutes les modifications ont ete sauvegardees correctement!")
    else:
        print("\n[ERROR] Les donnees sauvegardees ne correspondent pas!")
else:
    print("\n[ERROR] Profil non trouve dans le fichier sauvegarde!")

print("\n" + "=" * 50)
print("TEST TERMINE")
print("=" * 50)
