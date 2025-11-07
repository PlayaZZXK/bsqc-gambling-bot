import sqlite3
import json
from datetime import datetime
import os

class Database:
    def __init__(self, db_path=None):
        """Initialise la base de données SQLite"""
        # Utiliser /data si disponible (Render persistent disk), sinon ./data
        if db_path is None:
            if os.path.exists('/data'):
                db_path = '/data/economy.db'
            else:
                db_path = 'data/economy.db'
                os.makedirs('data', exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        self.create_tables()
        print(f"[DATABASE] Connecte a {db_path}")

    def create_tables(self):
        """Crée les tables si elles n'existent pas"""
        cursor = self.conn.cursor()

        # Table des profils utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                balance INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                gambling_profit INTEGER DEFAULT 0,
                total_wagered INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                games_lost INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                last_daily TEXT,
                daily_streak INTEGER DEFAULT 0,
                achievements TEXT DEFAULT '[]',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')

        # Table pour la loterie
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lottery (
                guild_id TEXT PRIMARY KEY,
                pot INTEGER DEFAULT 0,
                tickets TEXT DEFAULT '{}',
                draw_time TEXT,
                ticket_price INTEGER DEFAULT 50
            )
        ''')

        self.conn.commit()
        print("[DATABASE] Tables creees/verifiees")

    def get_user_profile(self, user_id, guild_id):
        """Récupère ou crée un profil utilisateur"""
        user_id = str(user_id)
        guild_id = str(guild_id)

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM users WHERE user_id = ? AND guild_id = ?
        ''', (user_id, guild_id))

        row = cursor.fetchone()

        if row is None:
            # Créer un nouveau profil
            cursor.execute('''
                INSERT INTO users (user_id, guild_id) VALUES (?, ?)
            ''', (user_id, guild_id))
            self.conn.commit()
            print(f"[DATABASE] Nouveau profil cree: user={user_id}, guild={guild_id}")

            # Récupérer le profil fraîchement créé
            cursor.execute('''
                SELECT * FROM users WHERE user_id = ? AND guild_id = ?
            ''', (user_id, guild_id))
            row = cursor.fetchone()

        # Convertir en dictionnaire
        profile = dict(row)
        profile['achievements'] = json.loads(profile['achievements'])
        return profile

    def update_user_profile(self, user_id, guild_id, **kwargs):
        """Met à jour un profil utilisateur - SAUVEGARDE INSTANTANÉE!"""
        user_id = str(user_id)
        guild_id = str(guild_id)

        # Construire la requête UPDATE dynamiquement
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        set_clause += ", updated_at = ?"

        values = list(kwargs.values())
        values.append(datetime.now().isoformat())
        values.extend([user_id, guild_id])

        cursor = self.conn.cursor()
        cursor.execute(f'''
            UPDATE users SET {set_clause}
            WHERE user_id = ? AND guild_id = ?
        ''', values)

        self.conn.commit()
        print(f"[DATABASE] Profil mis a jour: user={user_id}, fields={list(kwargs.keys())}")

        return cursor.rowcount > 0

    def modify_balance(self, user_id, guild_id, amount, reason=""):
        """Modifie le balance d'un utilisateur de manière sécurisée"""
        user_id = str(user_id)
        guild_id = str(guild_id)

        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE users
            SET balance = balance + ?, updated_at = ?
            WHERE user_id = ? AND guild_id = ?
        ''', (amount, datetime.now().isoformat(), user_id, guild_id))

        self.conn.commit()

        # Récupérer le nouveau balance
        cursor.execute('SELECT balance FROM users WHERE user_id = ? AND guild_id = ?',
                      (user_id, guild_id))
        new_balance = cursor.fetchone()[0]

        print(f"[DATABASE] Balance modifie: user={user_id}, montant={amount:+d}, nouveau={new_balance}")
        return new_balance

    def get_leaderboard(self, guild_id, limit=10, order_by='balance'):
        """Récupère le classement d'un serveur"""
        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT * FROM users
            WHERE guild_id = ?
            ORDER BY {order_by} DESC
            LIMIT ?
        ''', (str(guild_id), limit))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_user_rank(self, user_id, guild_id, order_by='balance'):
        """Récupère le rang d'un utilisateur dans un serveur"""
        user_id = str(user_id)
        guild_id = str(guild_id)

        cursor = self.conn.cursor()

        # Compter combien d'utilisateurs ont un meilleur score
        cursor.execute(f'''
            SELECT COUNT(*) + 1
            FROM users
            WHERE guild_id = ? AND {order_by} > (
                SELECT {order_by}
                FROM users
                WHERE user_id = ? AND guild_id = ?
            )
        ''', (guild_id, user_id, guild_id))

        rank = cursor.fetchone()[0]
        return rank if rank else None

    def get_global_stats(self):
        """Récupère les statistiques globales du bot"""
        cursor = self.conn.cursor()

        # Nombre de serveurs uniques
        cursor.execute('SELECT COUNT(DISTINCT guild_id) FROM users')
        total_guilds = cursor.fetchone()[0]

        # Nombre total d'utilisateurs
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        # Balance totale
        cursor.execute('SELECT SUM(balance) FROM users')
        total_balance = cursor.fetchone()[0] or 0

        # Total de parties jouées
        cursor.execute('SELECT SUM(games_played) FROM users')
        total_games = cursor.fetchone()[0] or 0

        # Total parié
        cursor.execute('SELECT SUM(total_wagered) FROM users')
        total_wagered = cursor.fetchone()[0] or 0

        return {
            'total_guilds': total_guilds,
            'total_users': total_users,
            'total_balance': total_balance,
            'total_games': total_games,
            'total_wagered': total_wagered
        }

    def backup_database(self):
        """Crée un backup de la base de données"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f'data/backup_{timestamp}.db'

        # Copier la base de données
        import shutil
        shutil.copy2(self.db_path, backup_path)
        print(f"[DATABASE] Backup cree: {backup_path}")
        return backup_path

    def close(self):
        """Ferme la connexion à la base de données"""
        self.conn.close()
        print("[DATABASE] Connexion fermee")

# Instance globale
db = Database()
