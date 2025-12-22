import sqlite3

db = r'C:\Users\Jhon\Downloads\app_cor\db.sqlite3'
conn = sqlite3.connect(db)
cursor = conn.cursor()

# Listar TODAS as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tabelas = cursor.fetchall()

print("📋 TODAS as tabelas do banco antigo:")
for t in tabelas:
    print(f"  - {t[0]}")
    
print(f"\n📊 Total: {len(tabelas)} tabelas")
    
conn.close()