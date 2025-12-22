from django.shortcuts import render
from django.http import JsonResponse
import requests

def matriz_decisoria(request):
    """View principal da Matriz Decisória"""
    return render(request, 'mapa_novo/matriz_decisoria.html')

def api_matriz_decisoria(request):
    """API para buscar dados da matriz decisória"""
    try:
        # Aqui você coloca a URL da sua API
        # response = requests.get('SUA_API_URL_AQUI')
        # dados = response.json()
        
        # Por enquanto, dados de exemplo
        dados = {
            "EstagioOperacional": {
                "EstagioOperacionalSugerido": 1,
                "ValorEstagioOperacionalSugerido": 0.36,
                "ProgressoEstagioOperacionalSugerido": 30
            },
            "NivelIndicado": {
                "NivelG1": 1,
                "NivelG2": 0,
                "NivelG3": 0,
                "NivelG4": 0,
                "NivelIndicado": 0.33,
                "ProximidadeNivelSeguinte": 27.5
            },
            "NivelG1": {
                "TabelaNivelG1": {
                    "NivelG1": 1,
                    "ProgressoNivelG1": 100,
                    "Chuva": {
                        "Total": 116,
                        "SemRegistro": 112,
                        "ChuvaFraca": 4,
                        "ChuvaModerada": 0,
                        "ChuvaForte": 0,
                        "ChuvaMuitoForte": 0
                    },
                    "Sirene": {
                        "Total": 162,
                        "Offline": 8,
                        "Desligada": 154,
                        "Alarmada": 0
                    }
                }
            },
            "NivelG2": {
                "ProgressoNivelG2": 73,
                "Critica": 0,
                "MuitoAlta": 0,
                "Alta": 0,
                "Media": 1,
                "Baixa": 11
            },
            "NivelG3": {
                "ProgressoNivelG3": 0,
                "StatusModal": {
                    "Metro": "Normal",
                    "BRT": "Normal",
                    "Trem": "Normal",
                    "Onibus": "Normal",
                    "Barcas": "Normal",
                    "VLT": "Normal",
                    "GIG": "Normal",
                    "SDU": "Normal"
                },
                "Transito": {
                    "EAC": 49,
                    "MCC": 0
                },
                "Modal": {
                    "ModalTotal": 8,
                    "ModalEmAtencao": 0,
                    "ModalInterrompido": 0
                }
            },
            "NivelG4": {
                "ProgressoNivelG4": 0,
                "MuitoAlta": 0,
                "Alta": 0,
                "Media": 0,
                "Baixa": 0,
                "Evento": None
            }
        }
        
        return JsonResponse(dados)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)