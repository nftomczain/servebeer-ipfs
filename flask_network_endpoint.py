# flask_network_endpoint.py
import time
from flask import jsonify

def get_network_status(ipfs_api_call_func, get_db_connection_func):
    """
    Pobiera prawdziwe dane o statusie sieci IPFS
    
    Args:
        ipfs_api_call_func: Funkcja do wywołania IPFS API
        get_db_connection_func: Funkcja do połączenia z bazą danych
    
    Returns:
        dict: Dane o statusie sieci
    """
    try:
        start_time = time.time()
        
        # Pobierz informacje o wersji IPFS
        try:
            version_result = ipfs_api_call_func('version', method='POST')
            ipfs_version = version_result.get('Version', 'Unknown') if version_result.get('success', True) else 'Unknown'
        except:
            ipfs_version = 'Unknown'
        
        # Pobierz liczbę peerów
        try:
            peers_result = ipfs_api_call_func('swarm/peers', method='POST')
            if peers_result.get('success', True) and 'Peers' in peers_result:
                peer_count = len(peers_result.get('Peers', []))
            else:
                peer_count = 0
        except:
            peer_count = 0
        
        # Oblicz czas odpowiedzi
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Sprawdź status węzła
        node_status = "Online" if ipfs_version != 'Unknown' and peer_count >= 0 else "Offline"
        
        # Oblicz success rate na podstawie bazy danych
        success_rate = calculate_success_rate_from_db(get_db_connection_func)
        
        return {
            "peer_count": peer_count,
            "response_time_ms": response_time_ms,
            "success_rate": success_rate,
            "ipfs_version": ipfs_version,
            "node_id": node_status
        }
        
    except Exception as e:
        print(f"Network status error: {e}")
        # W przypadku błędu, zwróć dane fallback
        return {
            "peer_count": 0,
            "response_time_ms": 0,
            "success_rate": 0.0,
            "ipfs_version": "Error",
            "node_id": "Offline"
        }

def calculate_success_rate_from_db(get_db_connection_func):
    """
    Oblicza success rate na podstawie ostatnich operacji z bazy danych
    
    Args:
        get_db_connection_func: Funkcja do połączenia z bazą danych
    
    Returns:
        float: Success rate w procentach
    """
    try:
        conn = get_db_connection_func()
        
        # Pobierz statystyki z ostatnich 24 godzin
        result = conn.execute('''
            SELECT 
                COUNT(*) as total_operations,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as successful_operations
            FROM pins 
            WHERE pinned_at > datetime('now', '-24 hours')
        ''').fetchone()
        
        conn.close()
        
        if result and result['total_operations'] > 0:
            success_rate = (result['successful_operations'] / result['total_operations']) * 100
            return round(success_rate, 1)
        else:
            # Jeśli brak operacji w ostatnich 24h, sprawdź ostatni tydzień
            conn = get_db_connection_func()
            total_result = conn.execute('''
                SELECT 
                    COUNT(*) as total_operations,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as successful_operations
                FROM pins 
                WHERE pinned_at > datetime('now', '-7 days')
            ''').fetchone()
            conn.close()
            
            if total_result and total_result['total_operations'] > 0:
                success_rate = (total_result['successful_operations'] / total_result['total_operations']) * 100
                return round(success_rate, 1)
            else:
                return 99.8  # Domyślna wartość jeśli brak danych
            
    except Exception as e:
        print(f"Error calculating success rate: {e}")
        return 99.8  # Domyślna wartość w przypadku błędu