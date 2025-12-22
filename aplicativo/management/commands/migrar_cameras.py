"""
Migra câmeras do banco antigo para o novo
"""
from django.core.management.base import BaseCommand
from aplicativo.models import Cameras
import sqlite3
import os

class Command(BaseCommand):
    help = 'Migra câmeras do sistema antigo'

    def handle(self, *args, **options):
        # Caminho do banco antigo
        db_antigo = r'C:\Users\Jhon\Downloads\app_cor\db.sqlite3'
        
        if not os.path.exists(db_antigo):
            self.stdout.write(self.style.ERROR(f'❌ Banco antigo não encontrado: {db_antigo}'))
            return
        
        try:
            # Conectar no banco antigo
            conn = sqlite3.connect(db_antigo)
            cursor = conn.cursor()
            
            # Buscar câmeras
            cursor.execute("""
                SELECT id, id_c, nome, bairro, lat, lon, status, criar
                FROM aplicativo_cameras
                WHERE lat IS NOT NULL AND lon IS NOT NULL
                ORDER BY id_c
            """)
            
            cameras_antigas = cursor.fetchall()
            conn.close()
            
            self.stdout.write(f'📥 Encontradas {len(cameras_antigas)} câmeras no sistema antigo')
            
            # Migrar
            contador = 0
            for row in cameras_antigas:
                id_old, id_c, nome, bairro, lat, lon, status, criar = row
                
                # Verificar se já existe
                if Cameras.objects.filter(id_c=id_c).exists():
                    continue
                
                # Criar
                Cameras.objects.create(
                    id_c=id_c,
                    nome=nome or f'Câmera {id_c}',
                    bairro=bairro or 'Sem bairro',
                    lat=lat,
                    lon=lon,
                    status=status or 'Não',
                    criar=criar
                )
                contador += 1
            
            self.stdout.write(self.style.SUCCESS(f'✅ {contador} câmeras migradas com sucesso!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro: {e}'))
            import traceback
            traceback.print_exc()