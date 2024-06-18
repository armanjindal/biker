# Multiple Lanes - change from dictionary to class based approach
import copy
import heapq

class GameState():
    """
    M: Number of bikes
    V: Minimum number of bikes to survive
    l0, l1, l2, l3: Lanes of the roads
    s: The initial starting speed from the game
    """
    def __init__(self, M,V, initial_speed, l0,l1,l2,l3, bike_data):
        self.x = 0
        self.turn = 0
        self.motorcycle_count = M
        self.num_alive = M # Assume all bikes are alive in the initial state and >= v
        self.min_survivors = V
        self.speed = initial_speed
        self.road = [l0,l1,l2,l3]
        self.road_length = len(l0)
        self.bike_data = bike_data

        # State variables for between turn
        self.is_jumping = False
        self.is_changing_up = False
        self.is_changing_down = False
        self.end_of_road = False
    
        # TODO: Optimization - create a state boolean for if it can change up or down
    
    def __str__(self):
        return f'Speed: {self.speed} Position: {self.x} Bike Data:{self.bike_data} Num Alive:{self.num_alive} End: {self.end_of_road} Num Survivors Min: {self.min_survivors}'
    
    def update_state_on_action(self, action):
        match action:
            case 'JUMP':
                self.is_jumping = True
            case 'SPEED':
                self.speed += 1
            case 'SLOW':
                if self.speed > 0:
                    self.speed -= 1
            case 'UP':
                if not self.is_top_lane_occupied():
                    self.is_changing_up = True
                    for data in self.bike_data.values():
                        data['Y'] -= 1
            case 'DOWN':
                if not self.is_bottom_lane_occupied():
                    self.is_changing_down = True
                    for data in self.bike_data.values():
                        data['Y'] += 1
            case 'WAIT':
                pass
            
        self.move_and_check_alive()
    
    def move_and_check_alive(self):
        for bike in self.bike_data.values():
            if not bike['A']:  # Skip dead bikes
                continue

            x_interval = self.x + self.speed
            if x_interval >= self.road_length: 
                self.end_of_road = True 
                x_interval = self.road_length - 1 

            if (self.switched_up_over_pothole(bike, x_interval) or \
                self.switched_down_over_pothole(bike, x_interval) or \
                self.jumped_on_pothole(bike, x_interval) or \
                self.drove_over_pothole(bike, x_interval)): 
                
                bike['A'] = False
                self.num_alive -= 1

        self.reset_state_variables()
        self.update_game_progress()


    def switched_up_over_pothole(self, bike, x_interval):
        # previous lane is bike['Y'] + 1
        return self.is_changing_up and (
            '0' in self.road[bike['Y'] + 1][self.x:x_interval] or
            '0' in self.road[bike['Y']][self.x:x_interval + 1]
        )

    def switched_down_over_pothole(self, bike, x_interval):
        # previous lane is bike['Y'] - 1
        return self.is_changing_down and (
            '0' in self.road[bike['Y'] - 1][self.x:x_interval] or
            '0' in self.road[bike['Y']][self.x:x_interval + 1]
        )

    def jumped_on_pothole(self, bike, x_interval):
        return self.is_jumping and self.road[bike['Y']][x_interval] == '0'

    def drove_over_pothole(self, bike, x_interval):
        return '0' in self.road[bike['Y']][self.x:x_interval + 1] and not self.is_jumping

    def reset_state_variables(self):
        self.is_changing_down = False 
        self.is_changing_up = False
        self.is_jumping = False 

    def update_game_progress(self):
        self.x += self.speed
        self.turn += 1
    
    def is_top_lane_occupied(self):
        for data in self.bike_data.values():
            if data['Y'] == 0:
                return True
    
    def is_bottom_lane_occupied(self):
        for data in self.bike_data.values():
            if data['Y'] == 3:
                return True
        
        return False

def find_valid_sequence(game):
    # Optimization - Limit actions based on logical constraints to manage exponential blow up
    # Removing WAIT as it is functionally equivalent to JUMP
    def valid_actions(game_state, action_squence):
        
        actions = ["SPEED", "JUMP"]  

        if game_state.speed > 2:
            actions.append("SLOW")
            #actions.append("WAIT")

        if not game_state.is_bottom_lane_occupied():
            actions.append("DOWN")
        if not game_state.is_top_lane_occupied():
            actions.append("UP")
    
        return actions

    priority_queue_optimization = True 
    def backtracking(action_sequence, game):
        if game.num_alive < game.min_survivors or game.turn > 50:
            return False
        
        if game.end_of_road:
            return action_sequence
        
        # Optimization - backtracking that pick the next action which maximizes the number of alive motorcycles
        if game.turn < 3:
            priority_queue = []
            for action in valid_actions(game, action_sequence):
                updated_game = copy.deepcopy(game)
                updated_game.update_state_on_action(action)                
                # Python heap default to min heap, invert the sign to make it a max heap
                heapq.heappush(priority_queue, (-updated_game.num_alive, action, updated_game))
            
            while priority_queue:
                _, action, updated_game = heapq.heappop(priority_queue)
                action_sequence.append(action)
                if backtracking(action_sequence, updated_game):
                    return action_sequence
                else:
                    action_sequence.pop()
        else:
            # Classic backtracking
            #print(action_sequence)
            for action in valid_actions(game, action_sequence):
                action_sequence.append(action)
                updated_game = copy.deepcopy(game)
                updated_game.update_state_on_action(action)
                if backtracking(action_sequence, updated_game):
                    return action_sequence
                else:
                    action_sequence.pop()
    
    
    return backtracking([], game)

test_cases = {
    '01-one_lonely_hole': {
        'M': 1,
        'V': 1,
        'initial_speed': 1,
        'l0': '..............................',
        'l1': '..............................',
        'l2': '...........0..................',
        'l3': '..............................',
        'bike_data': {
            0: {'Y': 2, 'A': True}
        }
    }, 
    '02-chained_jumps_increasing_length': {
        'M': 4,
        'V': 4,
        'initial_speed': 1,
        'l0': '..........000......0000..............000000.............',
        'l1': '..........000......0000..............000000.............',
        'l2': '..........000......0000..............000000.............',
        'l3': '..........000......0000..............000000.............',
        'bike_data': {
            0: {'Y': 0, 'A': True},
            1: {'Y': 1, 'A': True},
            2: {'Y': 2, 'A': True},
            3: {'Y': 3, 'A': True}
        }
    },
    '03-chained_jumps_decreasing_length': {
        'M': 4,
        'V': 4,
        'initial_speed': 8,
        'l0': '..............00000......0000.....00......',
        'l1': '..............00000......0000.....00......',
        'l2': '..............00000......0000.....00......',
        'l3': '..............00000......0000.....00......',
        'bike_data': {
            0: {'Y': 0, 'A': True},
            1: {'Y': 1, 'A': True},
            2: {'Y': 2, 'A': True},
            3: {'Y': 3, 'A': True}
        }
    },
    '04-chained_jumps_equal_length':{
        'M': 4,
        'V': 4,
        'initial_speed': 1,
        'l0': '..............00..00..00............',
        'l1': '..............00..00..00............',
        'l2': '..............00..00..00............',
        'l3': '..............00..00..00............',
        'bike_data': {
            0: {'Y': 0, 'A': True},
            1: {'Y': 1, 'A': True},
            2: {'Y': 2, 'A': True},
            3: {'Y': 3, 'A': True}
        }
    },
    '05-diagonial-columns':{
        'M': 4,
        'V': 3,
        'initial_speed': 6,
        'l0': '.............0.............0........',
        'l1': '..............0.............0.......',
        'l2': '...............0.............0......',
        'l3': '................0..........000......',
        'bike_data': {
            0: {'Y': 0, 'A': True},
            1: {'Y': 1, 'A': True},
            2: {'Y': 2, 'A': True},
            3: {'Y': 3, 'A': True}
        }
    },
    '06-scatter-pits':{
        'M': 2,
        'V': 2,
        'initial_speed': 2,
        'l0': '...0......0....0........0..0..0..0.....',
        'l1': '....0............000........0...0......',
        'l2': '.....0..........000..........0.0.......',
        'l3': '....0......0....0........0..0..0..0.....',
        'bike_data': {
            1: {'Y': 1, 'A': True},
            2: {'Y': 2, 'A': True},
        }
    },
    '11-mandatory-sacrifice': {
        'M': 4,
        'V': 1,
        'l0': '...0........0........0000.....',
        'l1': '....00......0.0...............',
        'l2': '.....000.......00.............',
        'l3': '.............0.0..............',
        'bike_data': {
            0: {'Y': 0, 'A': True},
            1: {'Y': 1, 'A': True},
            2: {'Y': 2, 'A': True},
            3: {'Y': 3, 'A': True}
        },
        'initial_speed': 3
    },
    '12-well-worn-road': {
    'M': 2, 
    'V': 1, 
    'l0': '................000000000........00000........000.............00.', 
    'l1': '.0.0..................000....000......0.0..................00000.', 
    'l2': '....000.........0.0...000................000............000000.0.', 
    'l3': '............0.000000...........0000...............0.0.....000000.', 
    'bike_data': {0: {'Y': 1, 'A': True}, 1: {'Y': 2, 'A': True}}, 
    'initial_speed': 1
}
}


def main():
    for case_name, case_data in test_cases.items():
        game = GameState(**case_data)
        valid_sequence = find_valid_sequence(game)
        print(f'Test Case: {case_name}')
        print(f'Valid Sequence: {valid_sequence}')
        print('-----------------------------------')

if __name__ == '__main__':
    main()

