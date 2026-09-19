ROOM_CAPACITIES = {
    269: 33, # 35
    438: 35, # 37
    365: 38, # 41
    455: 28, # 30
      2: 28, # 31
    377: 23, # 25
    270: 18, # 21
    258: 18, # 21
    376: 18, # 21
}

def get_available_room(remaining_places: dict):
    """
    Finds the first available room with a free seat.
    Returns the room number, updated remaining places, and a boolean indicating availability.
    """
    available_room = None
    for room_number, seat in remaining_places.items():
        if seat:
            available_room = room_number
            remaining_places[room_number] -= 1
            break
    
    if available_room is None:
        return available_room, remaining_places, False

    return available_room, remaining_places, True
