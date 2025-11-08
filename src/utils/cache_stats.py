"""
Utility per monitoring e logging statistiche cache.
"""

from ..logger import get_logger

logger = get_logger(__name__)


def log_cache_stats(cache_name, stats):
    """
    Logga statistiche cache in formato leggibile.

    Args:
        cache_name: Nome cache (es. "Cover Cache", "Page Cache")
        stats: Dict con statistiche da get_stats()
    """
    logger.info(
        f"{cache_name} Stats: "
        f"Hit Rate: {stats['hit_rate']:.1f}% | "
        f"Requests: {stats['total_requests']} (H:{stats['hits']}/M:{stats['misses']}) | "
        f"Usage: {stats['usage']:.1f}% ({stats['size']}/{stats['capacity']})"
    )


def should_log_stats(request_count, interval=100):
    """
    Determina se è il momento di loggare statistiche.

    Args:
        request_count: Numero totale richieste
        interval: Intervallo di logging (default ogni 100 richieste)

    Returns:
        True se dovrebbe loggare
    """
    return request_count > 0 and request_count % interval == 0


def analyze_cache_performance(stats):
    """
    Analizza performance cache e suggerisce ottimizzazioni.

    Args:
        stats: Dict statistiche cache

    Returns:
        Dict con analisi e suggerimenti
    """
    analysis = {
        'performance': 'good',
        'suggestions': []
    }

    hit_rate = stats['hit_rate']
    usage = stats['usage']

    # Analizza hit rate
    if hit_rate < 50:
        analysis['performance'] = 'poor'
        analysis['suggestions'].append(
            f"Hit rate basso ({hit_rate:.1f}%). Considerare aumento capacity."
        )
    elif hit_rate < 70:
        analysis['performance'] = 'fair'
        analysis['suggestions'].append(
            f"Hit rate medio ({hit_rate:.1f}%). Possibile miglioramento."
        )
    else:
        analysis['performance'] = 'excellent'

    # Analizza usage
    if usage > 90:
        analysis['suggestions'].append(
            f"Cache quasi piena ({usage:.1f}%). Considerare aumento capacity."
        )
    elif usage < 30 and stats['total_requests'] > 100:
        analysis['suggestions'].append(
            f"Cache sottoutilizzata ({usage:.1f}%). Capacity potrebbe essere ridotta."
        )

    return analysis
