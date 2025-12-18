"""
Script para visualizar cómo funciona el decaimiento espacial de incidentes.
Muestra cómo un reporte afecta a múltiples estaciones con diferentes impactos.
"""

import math
import matplotlib.pyplot as plt
import numpy as np


def calculate_impact_factor(distance_km: float) -> float:
    """
    Calcula el factor de impacto basado en distancia.
    Fórmula gaussiana: impact = exp(-(distance/20)^2)
    
    Args:
        distance_km: Distancia en kilómetros
        
    Returns:
        Factor de impacto entre 0.0 y 1.0
    """
    return math.exp(-(distance_km / 20) ** 2)


def plot_distance_decay():
    """Grafica la curva de decaimiento por distancia."""
    distances = np.linspace(0, 50, 100)
    impacts = [calculate_impact_factor(d) for d in distances]
    
    plt.figure(figsize=(12, 6))
    
    # Gráfica principal
    plt.subplot(1, 2, 1)
    plt.plot(distances, impacts, 'b-', linewidth=2, label='Impacto Gaussiano')
    plt.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='50% impacto')
    plt.axhline(y=0.1, color='orange', linestyle='--', alpha=0.5, label='10% impacto')
    
    # Marcar puntos clave
    key_distances = [0, 10, 20, 30, 40, 50]
    for d in key_distances:
        impact = calculate_impact_factor(d)
        plt.plot(d, impact, 'ro', markersize=8)
        plt.annotate(f'{d}km\n{impact:.1%}', 
                    xy=(d, impact), 
                    xytext=(d, impact + 0.1),
                    ha='center',
                    fontsize=9,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))
    
    plt.xlabel('Distancia (km)', fontsize=12)
    plt.ylabel('Factor de Impacto', fontsize=12)
    plt.title('Decaimiento Espacial del Impacto de Incidentes', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.ylim(-0.05, 1.1)
    
    # Tabla de valores
    plt.subplot(1, 2, 2)
    plt.axis('off')
    
    table_data = []
    table_data.append(['Distancia', 'Impacto', 'Ejemplo Severidad'])
    table_data.append(['(km)', '(%)', 'Media = 0.6'])
    table_data.append(['-'*10, '-'*10, '-'*15])
    
    for d in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]:
        impact = calculate_impact_factor(d)
        adjusted = 0.6 * impact  # Asumiendo severidad media
        table_data.append([f'{d}', f'{impact:.1%}', f'{adjusted:.3f}'])
    
    table = plt.table(cellText=table_data, 
                     cellLoc='center',
                     loc='center',
                     colWidths=[0.3, 0.3, 0.4])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Colorear encabezado
    for i in range(3):
        table[(0, i)].set_facecolor('#40466e')
        table[(0, i)].set_text_props(weight='bold', color='white')
        table[(1, i)].set_facecolor('#6366f1')
        table[(1, i)].set_text_props(color='white')
        table[(2, i)].set_facecolor('#e0e0e0')
    
    plt.title('Tabla de Impactos\n(Severidad Media = 0.6)', 
             fontsize=12, 
             fontweight='bold',
             pad=20)
    
    plt.tight_layout()
    plt.savefig('distance_decay_analysis.png', dpi=150, bbox_inches='tight')
    print("✅ Gráfica guardada: distance_decay_analysis.png")
    plt.show()


def simulate_incident_impact():
    """Simula el impacto de un incidente en estaciones cercanas."""
    print("\n" + "="*70)
    print("SIMULACIÓN: Impacto de un incidente en múltiples estaciones")
    print("="*70 + "\n")
    
    # Simular un incidente de severidad ALTA (0.9)
    base_severity = 0.9
    
    # Simular estaciones a diferentes distancias
    stations = [
        ("Estación A", 5),
        ("Estación B", 12),
        ("Estación C", 18),
        ("Estación D", 25),
        ("Estación E", 32),
        ("Estación F", 45),
        ("Estación G", 55),
    ]
    
    print(f"📍 INCIDENTE REPORTADO: Inundación (Severidad: ALTA = {base_severity})")
    print(f"🎯 Radio de influencia: 50km\n")
    print(f"{'Estación':<15} {'Distancia':<12} {'Factor':<10} {'Impacto Final':<15} {'Status'}")
    print("-" * 70)
    
    for station_name, distance in stations:
        if distance <= 50:
            impact_factor = calculate_impact_factor(distance)
            final_impact = base_severity * impact_factor
            status = "✅ Incluida" if final_impact > 0.01 else "⚠️ Muy débil"
            print(f"{station_name:<15} {distance:>4} km      {impact_factor:>5.1%}     {final_impact:>6.3f}          {status}")
        else:
            print(f"{station_name:<15} {distance:>4} km      {'N/A':<5}     {'N/A':<6}          ❌ Fuera de rango")
    
    print("\n💡 Interpretación:")
    print("   - Un solo incidente genera múltiples muestras de entrenamiento")
    print("   - Estaciones más cercanas tienen mayor peso en el aprendizaje")
    print("   - El modelo aprende patrones espaciales de propagación de riesgos")
    print()


def compare_old_vs_new():
    """Compara el sistema anterior (1 estación) vs el nuevo (múltiples estaciones)."""
    print("\n" + "="*70)
    print("COMPARACIÓN: Sistema Anterior vs Nuevo")
    print("="*70 + "\n")
    
    print("❌ ANTERIOR (1 estación más cercana):")
    print("   - 1 incidente → 1 muestra de entrenamiento")
    print("   - Solo afecta a la estación más cercana")
    print("   - No considera propagación espacial")
    print("   - Ejemplo: 10 incidentes = 10 muestras\n")
    
    print("✅ NUEVO (múltiples estaciones con decaimiento):")
    print("   - 1 incidente → ~5-10 muestras (dependiendo de densidad)")
    print("   - Afecta a TODAS las estaciones cercanas (<50km)")
    print("   - Impacto proporcional a distancia (gaussiano)")
    print("   - Ejemplo: 10 incidentes = ~50-100 muestras")
    print("   - Modelo aprende patrones espaciales realistas\n")
    
    print("📊 Ventajas del nuevo sistema:")
    print("   ✓ Mayor cantidad de datos de entrenamiento")
    print("   ✓ Representación realista de propagación de riesgos")
    print("   ✓ Estaciones sin reportes directos también aprenden")
    print("   ✓ Mejor generalización espacial")
    print()


if __name__ == "__main__":
    print("\n🔬 ANÁLISIS DE DECAIMIENTO ESPACIAL")
    print("="*70)
    
    # 1. Simulación de impacto
    simulate_incident_impact()
    
    # 2. Comparación
    compare_old_vs_new()
    
    # 3. Generar gráfica
    print("\n📈 Generando visualización...")
    try:
        plot_distance_decay()
    except Exception as e:
        print(f"⚠️ No se pudo generar gráfica (requiere matplotlib): {e}")
    
    print("\n" + "="*70)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*70 + "\n")
