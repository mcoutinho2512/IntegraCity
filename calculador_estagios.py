"""
calculador_estagios.py - Calcula estágios operacionais dinamicamente
"""

import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
django.setup()

from aplicativo.models import (
    DadosPlv, DadosMet, Ocorrencias, 
    Estagio, Evento, Calor
)

class CalculadorEstagios:
    """Calcula níveis operacionais do COR"""
    
    CORES = {
        1: {'cor': '#228d46', 'nome': 'Nível 1', 'descricao': 'Normalidade'},
        2: {'cor': '#f5c520', 'nome': 'Nível 2', 'descricao': 'Atenção'},
        3: {'cor': '#ef8c3f', 'nome': 'Nível 3', 'descricao': 'Alerta'},
        4: {'cor': '#d0262d', 'nome': 'Nível 4', 'descricao': 'Alerta Máximo'},
        5: {'cor': '#5f2f7e', 'nome': 'Nível 5', 'descricao': 'Crise'}
    }
    
    def calcular_nivel_chuva(self):
        """Calcula nível baseado em pluviômetros"""
        niveis = []
        
        pluviometros = DadosPlv.objects.order_by('-id')[:50]
        
        for plv in pluviometros:
            try:
                chuva = float(plv.chuva_1 or 0)
                
                if chuva >= 50:
                    niveis.append(5)
                elif chuva >= 25:
                    niveis.append(3)
                elif chuva >= 10:
                    niveis.append(2)
                elif chuva > 0:
                    niveis.append(1)
            except:
                continue
        
        return max(niveis) if niveis else 1
    
    def calcular_nivel_vento(self):
        """Calcula nível baseado em estações meteorológicas"""
        niveis = []
        
        estacoes = DadosMet.objects.order_by('-id')[:30]
        
        for est in estacoes:
            try:
                vel = float(est.vel or 0)
                
                if vel >= 60:
                    niveis.append(4)
                elif vel >= 40:
                    niveis.append(3)
                elif vel >= 20:
                    niveis.append(2)
            except:
                continue
        
        return max(niveis) if niveis else 1
    
    def calcular_nivel_temperatura(self):
        """Calcula nível baseado em sensação térmica"""
        niveis = []
        
        estacoes = DadosMet.objects.order_by('-id')[:30]
        
        for est in estacoes:
            try:
                temp = float(est.temp or 0)
                
                if temp >= 40:
                    niveis.append(3)
                elif temp >= 35:
                    niveis.append(2)
            except:
                continue
        
        return max(niveis) if niveis else 1
    
    def calcular_nivel_tempo(self):
        """Nível geral do TEMPO"""
        nivel_chuva = self.calcular_nivel_chuva()
        nivel_vento = self.calcular_nivel_vento()
        nivel_temp = self.calcular_nivel_temperatura()
        
        return max(nivel_chuva, nivel_vento, nivel_temp)
    
    def calcular_nivel_ocorrencias(self):
        """Nível baseado em ocorrências abertas"""
        try:
            abertas = Ocorrencias.objects.filter(status='Em andamento').count()
        except:
            abertas = Ocorrencias.objects.count()
        
        if abertas >= 50:
            return 5
        elif abertas >= 30:
            return 4
        elif abertas >= 15:
            return 3
        elif abertas >= 5:
            return 2
        else:
            return 1
    
    def calcular_nivel_eventos(self):
        """Nível baseado em eventos programados"""
        try:
            eventos_ativos = Evento.objects.filter(status='ativo').count()
        except:
            eventos_ativos = Evento.objects.count()
        
        if eventos_ativos >= 10:
            return 4
        elif eventos_ativos >= 5:
            return 3
        elif eventos_ativos >= 3:
            return 2
        elif eventos_ativos > 0:
            return 1
        else:
            return 1
    
    def calcular_nivel_calor(self):
        """Nível de alerta de calor"""
        try:
            calor_ativo = Calor.objects.filter(
                alive=True,
                data_f__isnull=True
            ).exists()
            
            return 3 if calor_ativo else 1
        except:
            return 1
    
    def calcular_nivel_mobilidade(self):
        """Nível de mobilidade (placeholder)"""
        return 1
    
    def salvar_estagio(self, resultado):
    """Salva o estágio calculado no banco"""
    try:
        from django.utils import timezone
        
        # Fechar estágios anteriores abertos
        Estagio.objects.filter(data_f__isnull=True).update(
            data_f=timezone.now()
        )
        
        # Criar novo estágio (campos mínimos)
        novo_estagio = Estagio(
            esta=resultado['nome'],
            data_i=timezone.now()
        )
        novo_estagio.save()
        
        print('✅ Estágio salvo no banco')
        return True
    except Exception as e:
        print(f'⚠️  Erro ao salvar: {e}')
        import traceback
        traceback.print_exc()
        return False
    
    def calcular_estagio_geral(self):
        """Calcula estágio operacional GERAL do COR"""
        
        nivel_tempo = self.calcular_nivel_tempo()
        nivel_ocorrencias = self.calcular_nivel_ocorrencias()
        nivel_eventos = self.calcular_nivel_eventos()
        nivel_mobilidade = self.calcular_nivel_mobilidade()
        nivel_calor = self.calcular_nivel_calor()
        
        niveis = [nivel_tempo, nivel_ocorrencias, nivel_eventos, nivel_mobilidade, nivel_calor]
        nivel_geral = int(sum(niveis) / len(niveis))
        
        resultado = {
            'nivel': nivel_geral,
            'cor': self.CORES[nivel_geral]['cor'],
            'nome': self.CORES[nivel_geral]['nome'],
            'descricao': self.CORES[nivel_geral]['descricao'],
            'detalhes': {
                'tempo': {'nivel': nivel_tempo, **self.CORES[nivel_tempo]},
                'ocorrencias': {'nivel': nivel_ocorrencias, **self.CORES[nivel_ocorrencias]},
                'eventos': {'nivel': nivel_eventos, **self.CORES[nivel_eventos]},
                'mobilidade': {'nivel': nivel_mobilidade, **self.CORES[nivel_mobilidade]},
                'calor': {'nivel': nivel_calor, **self.CORES[nivel_calor]}
            }
        }
        
        # Salvar no banco
        self.salvar_estagio(resultado)
        
        return resultado

if __name__ == '__main__':
    print('=' * 60)
    print('📊 CALCULANDO ESTÁGIOS OPERACIONAIS')
    print('=' * 60)
    
    calc = CalculadorEstagios()
    resultado = calc.calcular_estagio_geral()
    
    print(f"\n🎯 ESTÁGIO GERAL: {resultado['nome']}")
    print(f"   Cor: {resultado['cor']}")
    print(f"   {resultado['descricao']}")
    
    print('\n📋 DETALHES POR CATEGORIA:')
    for categoria, info in resultado['detalhes'].items():
        print(f"   • {categoria.title()}: Nível {info['nivel']} ({info['nome']})")
    
    print('\n' + '=' * 60)