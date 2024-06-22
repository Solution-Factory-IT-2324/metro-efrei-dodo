from backend.database.connection import connection

def get_all_metro_stations():
    db_connection = connection()
    cursor = db_connection.cursor(dictionary=True)

    query = """
        SELECT DISTINCT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.zone_id, s.location_type, s.parent_station
        FROM stops s
        JOIN stop_times st ON s.stop_id = st.stop_id
        JOIN trips t ON st.trip_id = t.trip_id
        JOIN routes r ON t.route_id = r.route_id
        WHERE r.route_type = 1
    """

    cursor.execute(query)
    metro_stations = cursor.fetchall()
    cursor.close()
    db_connection.close()

    return metro_stations