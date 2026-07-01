from pymavlink import mavutil
import time
import math

SITL_CONNECTION = 'udp:127.0.0.1:14551'

def get_location_offset(home_lat, home_lon, north_m, east_m):
    earth_radius = 6378137.0
    lat = home_lat + (north_m / earth_radius) * (180 / math.pi)
    lon = home_lon + (east_m / (earth_radius * math.cos(math.radians(home_lat)))) * (180 / math.pi)
    return lat, lon

def wait_for_ack(conn, command):
    while True:
        msg = conn.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if msg and msg.command == command:
            return msg.result == 0

def arm_and_takeoff(conn, altitude_m):
    print("Waiting for GPS fix...")
    while True:
        msg = conn.recv_match(type='GPS_RAW_INT', blocking=True, timeout=5)
        if msg and msg.fix_type >= 3:
            print(f"GPS fix acquired (type {msg.fix_type})")
            break

    print("Setting GUIDED mode...")
    conn.mav.set_mode_send(
        conn.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        4
    )
    time.sleep(2)

    print("Arming motors...")
    conn.mav.command_long_send(
        conn.target_system, conn.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 1, 0, 0, 0, 0, 0, 0
    )
    wait_for_ack(conn, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM)
    time.sleep(2)

    print(f"Taking off to {altitude_m}m...")
    conn.mav.command_long_send(
        conn.target_system, conn.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0, 0, 0, 0, 0, 0, 0, altitude_m
    )
    wait_for_ack(conn, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF)

    while True:
        msg = conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=5)
        if msg:
            current_alt = msg.relative_alt / 1000.0
            print(f"  altitude: {current_alt:.1f}m / {altitude_m}m", end='\r')
            if current_alt >= altitude_m * 0.95:
                print(f"\nReached target altitude {current_alt:.1f}m")
                break

def goto_waypoint(conn, lat, lon, alt_m):
    conn.mav.send(mavutil.mavlink.MAVLink_set_position_target_global_int_message(
        0,
        conn.target_system, conn.target_component,
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
        0b0000111111111000,
        int(lat * 1e7), int(lon * 1e7), alt_m,
        0, 0, 0, 0, 0, 0, 0, 0
    ))

def distance_to_wp(conn, target_lat, target_lon):
    msg = conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=2)
    if not msg:
        return float('inf')
    curr_lat = msg.lat / 1e7
    curr_lon = msg.lon / 1e7
    dlat = (target_lat - curr_lat) * 111320
    dlon = (target_lon - curr_lon) * 111320 * math.cos(math.radians(curr_lat))
    return math.sqrt(dlat**2 + dlon**2)

def execute_mission(mission: dict):
    print(f"\nConnecting to ArduPilot SITL...")
    conn = mavutil.mavlink_connection(SITL_CONNECTION)
    conn.wait_heartbeat()
    print("Connected.")

    msg = conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=10)
    home_lat = msg.lat / 1e7
    home_lon = msg.lon / 1e7
    print(f"Home position: {home_lat:.6f}, {home_lon:.6f}")

    arm_and_takeoff(conn, mission["altitude_m"])

    for loop_i in range(mission["loops"]):
        print(f"\n--- Loop {loop_i + 1} of {mission['loops']} ---")
        for wp_i, wp in enumerate(mission["waypoints"]):
            lat, lon = get_location_offset(
                home_lat, home_lon,
                wp["lat_offset_m"],
                wp["lon_offset_m"]
            )
            print(f"  Flying to waypoint {wp_i + 1}")
            goto_waypoint(conn, lat, lon, mission["altitude_m"])

            while True:
                dist = distance_to_wp(conn, lat, lon)
                print(f"    distance: {dist:.1f}m", end='\r')
                if dist < 2.0:
                    print(f"\n    Waypoint {wp_i + 1} reached.")
                    break
                time.sleep(0.5)

    if mission["return_to_home"]:
        print("\nReturning to home...")
        conn.mav.command_long_send(
            conn.target_system, conn.target_component,
            mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
            0, 0, 0, 0, 0, 0, 0, 0
        )

	# wait until drone actually lands (altitude drops to near zero)
        print("Waiting for landing...")
        while True:
            msg = conn.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=5)
            if msg:
                alt = msg.relative_alt / 1000.0
                print(f"  altitude: {alt:.1f}m", end='\r')
                if alt < 0.3:
                    print("\nLanded.")
                    break
            time.sleep(0.5)

	# disarm motors after landing
        print("Disarming motors...")
        conn.mav.command_long_send(
            conn.target_system, conn.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, 0, 0, 0, 0, 0, 0, 0
        )
        time.sleep(2)

    print("\nMission complete.")
    conn.close()
