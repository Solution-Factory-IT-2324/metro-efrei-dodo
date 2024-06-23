from backend.database.connection import connection


def get_all_metro_stations():
    try:
        db_connection = connection()
        cursor = db_connection.cursor(dictionary=True)

        query = """
            SELECT DISTINCT s.stop_id, s.stop_name, s.stop_lat, s.stop_lon, s.zone_id, s.wheelchair_boarding
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
    except Exception as e:
        raise Exception(f"Error getting metro stations at BDD request : {str(e)}")


def get_stations_by_line_metro(line_id):
    try:
        db_connection = connection()
        cursor = db_connection.cursor(dictionary=True)

        # Query to get stations for the specific line, ordered by stop_sequence
        query = """
            SELECT
                s.stop_id,
                s.stop_name,
                st.stop_sequence AS stop_sequence,
                (0) as line_branch
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id
            JOIN trips t ON st.trip_id = t.trip_id
            JOIN routes r ON t.route_id = r.route_id
            WHERE r.route_short_name = %s
              AND t.direction_id = %s
              AND r.route_type = 1
              AND st.trip_id = (
                  SELECT MAX(st_inner.trip_id)
                  FROM stop_times st_inner
                  JOIN trips t_inner ON st_inner.trip_id = t_inner.trip_id
                  JOIN routes r_inner ON t_inner.route_id = r_inner.route_id
                  WHERE r_inner.route_short_name = %s
                    AND t_inner.direction_id = %s
                    AND r_inner.route_type = 1
              )
            ORDER BY st.stop_sequence;
        """

        cursor.execute(query, (line_id, 0, line_id, 0,))
        stations_1 = cursor.fetchall()

        cursor.execute(query, (line_id, 1, line_id, 1,))
        stations_2 = cursor.fetchall()
        stations_3, stations_4 = [dico for dico in stations_1], [dico for dico in stations_2]

        if not stations_1 and not stations_2:
            raise Exception(f"No stations found for line {line_id}")

        if stations_1[0]['stop_name'] != stations_2[-1]['stop_name']:
            for station in stations_1:
                # Check if the station name is in the other list
                if station['stop_name'] in [s['stop_name'] for s in stations_2]:
                    station['line_branch'] = 1
                    del stations_2[[s['stop_name'] for s in stations_2].index(station['stop_name'])]
                else:
                    station['line_branch'] = 0

            for station in stations_2:
                station['line_branch'] = 2
                stations_1.append(station)

        for station in stations_3:
            # Detect if there is stations deserved only in one direction
            if station['stop_name'] not in [s['stop_name'] for s in stations_4]:
                station['line_branch'] = 3
                # stations_1.append(station)

        for station in stations_4:
            if station['stop_name'] not in [s['stop_name'] for s in stations_3]:
                station['line_branch'] = 4
                stations_1.append(station)

        return stations_1
    except Exception as e:
        raise Exception(f"{str(e)}")
