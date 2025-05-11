import tkinter as tk
from tkinter import messagebox, ttk
import random

BOARD_SIZE = 10
SHIP_SIZES = [5, 4, 3, 3, 2]

class Cell:
    def __init__(self):
        self.has_ship = False
        self.hit = False

class Ship:
    def __init__(self, size):
        self.size = size
        self.positions = []

    def is_sunk(self, board):
        return all(board.grid[r][c].hit for r, c in self.positions)

class Board:
    def __init__(self):
        self.grid = [[Cell() for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.ships = []

    def place_ship(self, size):
        while True:
            orientation = random.choice(['H', 'V'])
            row = random.randint(0, BOARD_SIZE - 1)
            col = random.randint(0, BOARD_SIZE - 1)
            positions = []
            for i in range(size):
                r = row + (i if orientation == 'V' else 0)
                c = col + (i if orientation == 'H' else 0)
                if r >= BOARD_SIZE or c >= BOARD_SIZE or self.grid[r][c].has_ship:
                    break
                positions.append((r, c))
            else:
                for r, c in positions:
                    self.grid[r][c].has_ship = True
                ship = Ship(size)
                ship.positions = positions
                self.ships.append(ship)
                break

    def all_ships_sunk(self):
        return all(self.grid[r][c].hit for ship in self.ships for r, c in ship.positions)
        
    def find_ship_by_position(self, r, c):
        """Find which ship is at the given position"""
        for ship in self.ships:
            if (r, c) in ship.positions:
                return ship
        return None

def enhanced_monte_carlo_attack(player, opponent_board, simulations=1000):
    # First check if there are any hit ships that aren't sunk yet
    unsunk_hits = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if opponent_board.grid[r][c].hit and opponent_board.grid[r][c].has_ship:
                ship = opponent_board.find_ship_by_position(r, c)
                if ship and not ship.is_sunk(opponent_board):
                    unsunk_hits.append((r, c))
    
    # If we have unsunk ships with hits, target adjacent cells
    if unsunk_hits:
        # Group hits by ship
        ship_hits = {}
        for r, c in unsunk_hits:
            ship = opponent_board.find_ship_by_position(r, c)
            if ship:
                ship_id = id(ship)
                if ship_id not in ship_hits:
                    ship_hits[ship_id] = []
                ship_hits[ship_id].append((r, c))
        
        # For each ship with hits, find the adjacent cells to target
        potential_targets = []
        for ship_id, hits in ship_hits.items():
            # Check if hits are in a line
            is_horizontal = all(hit[0] == hits[0][0] for hit in hits)
            is_vertical = all(hit[1] == hits[0][1] for hit in hits)
            
            if len(hits) > 1 and (is_horizontal or is_vertical):
                # For horizontal ships
                if is_horizontal:
                    row = hits[0][0]
                    cols = [hit[1] for hit in hits]
                    min_col, max_col = min(cols), max(cols)
                    
                    # Check left and right
                    if min_col - 1 >= 0 and not opponent_board.grid[row][min_col - 1].hit:
                        potential_targets.append((row, min_col - 1))
                    if max_col + 1 < BOARD_SIZE and not opponent_board.grid[row][max_col + 1].hit:
                        potential_targets.append((row, max_col + 1))
                
                # For vertical ships
                elif is_vertical:
                    col = hits[0][1]
                    rows = [hit[0] for hit in hits]
                    min_row, max_row = min(rows), max(rows)
                    
                    # Check above and below
                    if min_row - 1 >= 0 and not opponent_board.grid[min_row - 1][col].hit:
                        potential_targets.append((min_row - 1, col))
                    if max_row + 1 < BOARD_SIZE and not opponent_board.grid[max_row + 1][col].hit:
                        potential_targets.append((max_row + 1, col))
            else:
                # Single hit or non-linear hits, check all four directions
                for r, c in hits:
                    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and 
                            not opponent_board.grid[nr][nc].hit):
                            potential_targets.append((nr, nc))
        
        # If we have potential targets, choose one randomly
        if potential_targets:
            return random.choice(potential_targets)
    
    # If no unsunk hits or no valid adjacent cells, fall back to Monte Carlo strategy
    heatmap = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    known_hits = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
                  if opponent_board.grid[r][c].hit and opponent_board.grid[r][c].has_ship]
    known_misses = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
                    if opponent_board.grid[r][c].hit and not opponent_board.grid[r][c].has_ship]

    def valid_placement(r, c, size, orientation, used):
        positions = []
        for i in range(size):
            nr, nc = r + (i if orientation == 'V' else 0), c + (i if orientation == 'H' else 0)
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                return None
            if (nr, nc) in used or (nr, nc) in known_misses:
                return None
            positions.append((nr, nc))
        if known_hits and not any(hit in positions for hit in known_hits):
            return None
        return positions

    for _ in range(simulations):
        temp_used = set()
        valid = True
        for size in SHIP_SIZES:
            placed = False
            for _ in range(100):
                orientation = random.choice(['H', 'V'])
                r, c = random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1)
                pos = valid_placement(r, c, size, orientation, temp_used)
                if pos:
                    temp_used.update(pos)
                    placed = True
                    break
            if not placed:
                valid = False
                break
        if not valid:
            continue
        for r, c in temp_used:
            if (r, c) not in known_hits and (r, c) not in known_misses:
                heatmap[r][c] += 1

    max_val = max(max(row) for row in heatmap)
    candidates = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
                  if heatmap[r][c] == max_val and not opponent_board.grid[r][c].hit]
    return random.choice(candidates) if candidates else random.choice(
        [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
         if not opponent_board.grid[r][c].hit])

class Player:
    def __init__(self, is_user=False):
        self.board = Board()
        self.is_user = is_user
        self.used_coords = set()
        self.target_queue = []
        self.current_hunt = []  # Track cells being targeted for current ship
        self.powerups = {
            'Missile': 3,
            'Destroyer': 1,
            'Intel': 2
        }

class BattleshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Battleship")
        self.user = Player(is_user=True)
        self.computer = Player()
        self.turn = 0
        self.powerup_mode = None
        self.difficulty = "Hard"  # Default to Hard difficulty
        self.last_hit = None  # For Easy mode tracking

        # Create difficulty selection before starting the game
        self.setup_frame = tk.Frame(self.root)
        self.setup_frame.pack(pady=20)
        
        tk.Label(self.setup_frame, text="Select Difficulty:").grid(row=0, column=0, padx=10)
        self.diff_var = tk.StringVar(value="Hard")
        diff_combo = ttk.Combobox(self.setup_frame, textvariable=self.diff_var, values=["Easy", "Hard"])
        diff_combo.grid(row=0, column=1, padx=10)
        
        tk.Button(self.setup_frame, text="Start Game", command=self.start_game).grid(row=1, column=0, columnspan=2, pady=20)

    def start_game(self):
        self.difficulty = self.diff_var.get()
        self.setup_frame.destroy()
        
        for size in SHIP_SIZES:
            self.user.board.place_ship(size)
            self.computer.board.place_ship(size)

        self.status = tk.Label(self.root, text=f"Game Started - {self.difficulty} Mode - Your Turn")
        self.status.grid(row=0, column=0, columnspan=20)

        tk.Label(self.root, text="Enemy Board").grid(row=1, column=0, columnspan=10)
        tk.Label(self.root, text="Your Board").grid(row=1, column=11, columnspan=10)

        self.enemy_frame = tk.Frame(self.root)
        self.enemy_frame.grid(row=2, column=0, columnspan=10)
        tk.Label(self.root, text=" " * 5).grid(row=2, column=10)
        self.user_frame = tk.Frame(self.root)
        self.user_frame.grid(row=2, column=11, columnspan=10)

        self.enemy_buttons = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.user_buttons = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                e_btn = tk.Button(self.enemy_frame, width=2, height=1,
                                  command=lambda r=r, c=c: self.enemy_clicked(r, c))
                e_btn.grid(row=r, column=c)
                self.enemy_buttons[r][c] = e_btn

                u_btn = tk.Button(self.user_frame, width=2, height=1)
                u_btn.grid(row=r, column=c)
                if self.user.board.grid[r][c].has_ship:
                    u_btn.config(bg='gray')
                self.user_buttons[r][c] = u_btn

        powerup_frame = tk.Frame(self.root)
        powerup_frame.grid(row=3, column=0, columnspan=20, pady=10)
        
        # Display difficulty
        difficulty_label = tk.Label(powerup_frame, text=f"Difficulty: {self.difficulty}")
        difficulty_label.pack(side=tk.RIGHT, padx=10)
        
        # Powerup buttons
        self.powerup_buttons = {}
        self.powerup_buttons['Missile'] = tk.Button(powerup_frame, text="Missile (3)", command=lambda: self.set_powerup('Missile'))
        self.powerup_buttons['Missile'].pack(side=tk.LEFT, padx=5)
        self.powerup_buttons['Destroyer'] = tk.Button(powerup_frame, text="Destroyer (1)", command=lambda: self.set_powerup('Destroyer'))
        self.powerup_buttons['Destroyer'].pack(side=tk.LEFT, padx=5)
        self.powerup_buttons['Intel'] = tk.Button(powerup_frame, text="Intel (2)", command=lambda: self.set_powerup('Intel'))
        self.powerup_buttons['Intel'].pack(side=tk.LEFT, padx=5)

    def set_powerup(self, kind):
        if self.user.powerups[kind] > 0:
            self.powerup_mode = kind
            self.status.config(text=f"{kind} selected! Click a cell to use.")
        else:
            self.status.config(text=f"No {kind}s left!")

    def enemy_clicked(self, r, c):
        if self.turn % 2 != 0:
            return

        if self.powerup_mode:
            self.use_powerup(r, c)
            return

        cell = self.computer.board.grid[r][c]
        if cell.hit:
            return
        cell.hit = True
        self.update_button(r, c, cell, self.enemy_buttons)
        self.check_ship_sunk(self.computer.board, self.enemy_buttons)
        self.status.config(text=f"You {'hit!' if cell.has_ship else 'missed.'}")
        if self.computer.board.all_ships_sunk():
            messagebox.showinfo("Game Over", "You Win!")
            self.root.quit()
        else:
            self.turn += 1
            self.root.after(1000, self.computer_turn)

    def use_powerup(self, r, c):
        kind = self.powerup_mode
        if self.user.powerups[kind] <= 0:
            self.status.config(text=f"No {kind}s left!")
            self.powerup_mode = None
            return

        if kind == 'Missile':
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                        cell = self.computer.board.grid[nr][nc]
                        if not cell.hit:
                            cell.hit = True
                            self.update_button(nr, nc, cell, self.enemy_buttons)
        elif kind == 'Destroyer':
            for i in range(BOARD_SIZE):
                cell = self.computer.board.grid[r][i]
                if not cell.hit:
                    cell.hit = True
                    self.update_button(r, i, cell, self.enemy_buttons)
        elif kind == 'Intel':
            shots = 0
            while shots < 5:
                rr, cc = random.randint(0, 9), random.randint(0, 9)
                cell = self.computer.board.grid[rr][cc]
                if not cell.hit:
                    cell.hit = True
                    self.update_button(rr, cc, cell, self.enemy_buttons)
                    shots += 1

        self.user.powerups[kind] -= 1
        self.powerup_buttons[kind].config(text=f"{kind} ({self.user.powerups[kind]})")
        if self.user.powerups[kind] == 0:
            self.powerup_buttons[kind].config(state=tk.DISABLED)

        self.check_ship_sunk(self.computer.board, self.enemy_buttons)
        self.status.config(text=f"{kind} used.")
        self.powerup_mode = None
        if self.computer.board.all_ships_sunk():
            messagebox.showinfo("Game Over", "You Win!")
            self.root.quit()
        else:
            self.turn += 1
            self.root.after(1000, self.computer_turn)

    def computer_turn(self):
        if self.difficulty == "Hard":
            self.hard_mode_turn()
        else:
            self.easy_mode_turn()

    def easy_mode_turn(self):
        # Random chance to use a powerup
        if random.random() < 0.4:  # 40% chance to use a powerup
            available_powerups = [p for p, count in self.computer.powerups.items() if count > 0]
            if available_powerups:
                powerup = random.choice(available_powerups)
                self.use_computer_powerup(powerup)
                return

        # First check if we need to clear the target queue if we've sunk ships
        self.clear_sunk_ship_targets()
        
        # If we have targets in the queue (from previous hits), use those first
        if self.computer.target_queue:
            r, c = self.computer.target_queue.pop(0)
            # Skip invalid or already-hit cells
            while (r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE 
                  or self.user.board.grid[r][c].hit):
                if not self.computer.target_queue:
                    # If all targets are invalid, pick a random cell
                    r, c = self.get_random_unhit_cell()
                    break
                r, c = self.computer.target_queue.pop(0)
        else:
            # Random shot if no targets
            r, c = self.get_random_unhit_cell()

        cell = self.user.board.grid[r][c]
        cell.hit = True
        self.update_button(r, c, cell, self.user_buttons)

        # If it's a hit, add adjacent cells to the target queue
        if cell.has_ship:
            self.last_hit = (r, c)
            self.computer.current_hunt.append((r, c))
            
            # Add adjacent cells to target queue
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and 
                    not self.user.board.grid[nr][nc].hit and
                    (nr, nc) not in self.computer.target_queue):
                    self.computer.target_queue.append((nr, nc))
            
            # If we have more than one hit on the same ship, prioritize in-line shots
            if len(self.computer.current_hunt) > 1:
                self.prioritize_inline_targets(r, c)
        
        self.finish_computer_turn()

    def clear_sunk_ship_targets(self):
        # Check if we need to clear target queue because we've completed a ship
        if self.computer.current_hunt:
            # Check if all positions in current_hunt belong to the same ship
            sample_r, sample_c = self.computer.current_hunt[0]
            ship = self.user.board.find_ship_by_position(sample_r, sample_c)
            
            if ship and ship.is_sunk(self.user.board):
                # Clear current hunt and target queue if ship is sunk
                self.computer.current_hunt = []
                self.computer.target_queue = []
                self.last_hit = None

    def prioritize_inline_targets(self, r, c):
        """Prioritize targets that are in line with existing hits"""
        if len(self.computer.current_hunt) < 2:
            return
            
        # Determine if hits are in a horizontal or vertical line
        is_horizontal = all(hit[0] == self.computer.current_hunt[0][0] for hit in self.computer.current_hunt)
        is_vertical = all(hit[1] == self.computer.current_hunt[0][1] for hit in self.computer.current_hunt)
        
        if is_horizontal:
            # Prioritize cells on the same row
            row = self.computer.current_hunt[0][0]
            cols = [hit[1] for hit in self.computer.current_hunt]
            min_col, max_col = min(cols), max(cols)
            
            # Clear current queue
            self.computer.target_queue = []
            
            # Add cells to left and right
            if min_col - 1 >= 0 and not self.user.board.grid[row][min_col - 1].hit:
                self.computer.target_queue.append((row, min_col - 1))
            if max_col + 1 < BOARD_SIZE and not self.user.board.grid[row][max_col + 1].hit:
                self.computer.target_queue.append((row, max_col + 1))
                
        elif is_vertical:
            # Prioritize cells in the same column
            col = self.computer.current_hunt[0][1]
            rows = [hit[0] for hit in self.computer.current_hunt]
            min_row, max_row = min(rows), max(rows)
            
            # Clear current queue
            self.computer.target_queue = []
            
            # Add cells above and below
            if min_row - 1 >= 0 and not self.user.board.grid[min_row - 1][col].hit:
                self.computer.target_queue.append((min_row - 1, col))
            if max_row + 1 < BOARD_SIZE and not self.user.board.grid[max_row + 1][col].hit:
                self.computer.target_queue.append((max_row + 1, col))

    def get_random_unhit_cell(self):
        unhit_cells = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) 
                       if not self.user.board.grid[r][c].hit]
        return random.choice(unhit_cells)

    def hard_mode_turn(self):
        # Random chance to use a powerup
        if random.random() < 0.75:  # 30% chance to use a powerup in hard mode
            available_powerups = [p for p, count in self.computer.powerups.items() if count > 0]
            if available_powerups:
                powerup = random.choice(available_powerups)
                self.use_computer_powerup(powerup)
                return

        # Use enhanced Monte Carlo algorithm for targeting
        r, c = enhanced_monte_carlo_attack(self.computer, self.user.board)
        cell = self.user.board.grid[r][c]
        cell.hit = True
        self.update_button(r, c, cell, self.user_buttons)
        
        self.finish_computer_turn()

    def use_computer_powerup(self, kind):
        self.computer.powerups[kind] -= 1
        hits_found = False
        
        if kind == 'Missile':
            # Use enhanced Monte Carlo in hard mode for better targeting
            r, c = enhanced_monte_carlo_attack(self.computer, self.user.board) if self.difficulty == "Hard" else self.get_random_unhit_cell()
            affected_positions = []
            
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                        cell = self.user.board.grid[nr][nc]
                        if not cell.hit:
                            cell.hit = True
                            self.update_button(nr, nc, cell, self.user_buttons)
                            if cell.has_ship and self.difficulty == "Easy":
                                hits_found = True
                                affected_positions.append((nr, nc))
            
            # Add hits to current hunt for tracking
            if self.difficulty == "Easy" and affected_positions:
                self.computer.current_hunt.extend(affected_positions)
                self.last_hit = affected_positions[-1]
                self.update_target_queue_after_powerup()
            
            self.status.config(text="Computer used Missile!")
            
        elif kind == 'Destroyer':
            # In hard mode, use enhanced Monte Carlo to find a promising row
            if self.difficulty == "Hard":
                best_row = -1
                max_score = -1
                
                # Evaluate each row
                for row in range(BOARD_SIZE):
                    unhit_cells = [(row, c) for c in range(BOARD_SIZE) if not self.user.board.grid[row][c].hit]
                    if not unhit_cells:
                        continue
                    
                    # Count hits on this row to prioritize rows with hits
                    hit_count = sum(1 for c in range(BOARD_SIZE)
                                   if self.user.board.grid[row][c].hit and self.user.board.grid[row][c].has_ship)
                    
                    # Score based on unhit cells and existing hits
                    score = len(unhit_cells) + hit_count * 2
                    
                    if score > max_score:
                        max_score = score
                        best_row = row
                
                # If no good row found, choose random
                r = best_row if best_row != -1 else random.randint(0, BOARD_SIZE - 1)
            else:
                r = random.randint(0, BOARD_SIZE - 1)
                
            affected_positions = []
            
            for c in range(BOARD_SIZE):
                cell = self.user.board.grid[r][c]
                if not cell.hit:
                    cell.hit = True
                    self.update_button(r, c, cell, self.user_buttons)
                    if cell.has_ship and self.difficulty == "Easy":
                        hits_found = True
                        affected_positions.append((r, c))
            
            # Add hits to current hunt for tracking
            if self.difficulty == "Easy" and affected_positions:
                self.computer.current_hunt.extend(affected_positions)
                self.last_hit = affected_positions[-1]
                self.update_target_queue_after_powerup()
            
            self.status.config(text=f"Computer used Destroyer on row {r+1}!")
            
        elif kind == 'Intel':
            shots = 0
            affected_positions = []
            
            # In hard mode, use more strategic intel
            if self.difficulty == "Hard":
                # Create a probability map
                for _ in range(5):
                    r, c = enhanced_monte_carlo_attack(self.computer, self.user.board)
                    cell = self.user.board.grid[r][c]
                    if not cell.hit:
                        cell.hit = True
                        self.update_button(r, c, cell, self.user_buttons)
                        shots += 1
            else:
                while shots < 5:
                    r, c = self.get_random_unhit_cell()
                    cell = self.user.board.grid[r][c]
                    cell.hit = True
                    self.update_button(r, c, cell, self.user_buttons)
                    shots += 1
                    if cell.has_ship:
                        hits_found = True
                        affected_positions.append((r, c))
            
            # Add hits to current hunt for tracking
            if self.difficulty == "Easy" and affected_positions:
                self.computer.current_hunt.extend(affected_positions)
                self.last_hit = affected_positions[-1]
                self.update_target_queue_after_powerup()
            
            self.status.config(text="Computer used Intel to scan 5 cells!")
        
        self.finish_computer_turn()

    def update_target_queue_after_powerup(self):
        """Update target queue after powerup use"""
        # First check if any ships were sunk
        self.clear_sunk_ship_targets()
        
        # If we have current hunt coordinates, add adjacent cells
        if self.computer.current_hunt:
            # Create a fresh target queue
            self.computer.target_queue = []
            
            # Try to identify if hits are in line
            if len(self.computer.current_hunt) > 1:
                is_horizontal = all(hit[0] == self.computer.current_hunt[0][0] for hit in self.computer.current_hunt)
                is_vertical = all(hit[1] == self.computer.current_hunt[0][1] for hit in self.computer.current_hunt)
                
                if is_horizontal or is_vertical:
                    self.prioritize_inline_targets(self.computer.current_hunt[-1][0], self.computer.current_hunt[-1][1])
                    return
            
            # If no line pattern identified, add all adjacent cells
            for r, c in self.computer.current_hunt:
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and 
                        not self.user.board.grid[nr][nc].hit and
                        (nr, nc) not in self.computer.target_queue):
                        self.computer.target_queue.append((nr, nc))
            
            # Shuffle to make it less predictable
            random.shuffle(self.computer.target_queue)

    def finish_computer_turn(self):
        self.check_ship_sunk(self.user.board, self.user_buttons)
        if self.user.board.all_ships_sunk():
            messagebox.showinfo("Game Over", "Computer Wins!")
            self.root.quit()
        else:
            self.turn += 1
            self.status.config(text="Your Turn")

    def update_button(self, r, c, cell, button_grid):
        btn = button_grid[r][c]
        if cell.hit:
            btn.config(bg='red' if cell.has_ship else 'blue')

    def check_ship_sunk(self, board, button_grid):
        for ship in board.ships:
            if ship.is_sunk(board):
                for r, c in ship.positions:
                    button_grid[r][c].config(bg='darkred')

if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()