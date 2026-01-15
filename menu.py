import customtkinter as ctk
import subprocess
import sys
import random
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1000, 700
NEON_PINK = "#ff00ff"
NEON_CYAN = "#00ffff"

ctk.set_appearance_mode("dark")

class SpaceInvadersMenu:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Space Invaders: NEON EDITION")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.resizable(False, False)
        
        # Canvas for drawing
        self.canvas = ctk.CTkCanvas(self.root, width=WIDTH, height=HEIGHT, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Initialize Stars
        self.stars = self.create_stars(100)
        
        # Animation State
        self.pulse_alpha = 0
        self.pulse_direction = 1
        self.running = True  # Flag to stop animation on exit
        
        # Draw UI
        self.draw_interface()
        
        # Bindings
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Button-1>", self.on_click)
        
        # Start Animation
        self.root.after(100, self.animate)

        # Handle window closing cleanly
        self.root.protocol("WM_DELETE_WINDOW", self.quit_game)

    def create_stars(self, count):
        stars = []
        for _ in range(count):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(1, 3)
            speed = random.uniform(0.5, 3.0)
            item = self.canvas.create_oval(x, y, x+size, y+size, fill="white", outline="")
            stars.append({'id': item, 'speed': speed, 'x': x, 'y': y, 'size': size})
        return stars

    def draw_retro_logo(self, x, y, text):
        font_family = "Arial Black"
        # UPDATED: Reduced size from 80 to 64 to fit screen
        size = 64  
        
        # Shadow Layers
        for i in range(8, 0, -1):
            color = "#4a0072" if i > 4 else "#9400d3"
            self.canvas.create_text(x + i, y + i, text=text, fill=color, font=(font_family, size, "bold"))
        
        # Top Layer
        self.canvas.create_text(x, y, text=text, fill=NEON_PINK, font=(font_family, size, "bold"))
        
        # Scanlines (Adjusted width to match new text size)
        for i in range(y - 40, y + 40, 4):
            self.canvas.create_line(x - 280, i, x + 280, i, fill="black", stipple="gray25", width=1)

    def draw_interface(self):
        self.draw_retro_logo(WIDTH//2, 200, "SPACE INVADERS")
        self.canvas.create_text(WIDTH//2, 280, text="RETRO ARCADE SAGA", fill=NEON_CYAN, font=("Courier", 24, "bold"))

        # Button Box
        box_x, box_y = WIDTH//2, 450
        w, h = 400, 100
        
        # Glow
        for i in range(5):
            self.canvas.create_rectangle(
                box_x - w//2 - i, box_y - h//2 - i, 
                box_x + w//2 + i, box_y + h//2 + i, 
                outline=NEON_PINK, width=1
            )

        # Clickable Area
        self.play_btn_id = self.canvas.create_rectangle(
            box_x - w//2, box_y - h//2, 
            box_x + w//2, box_y + h//2, 
            fill="#110022", outline=NEON_CYAN, width=3,
            tags="play_btn"
        )
        
        # Text
        self.start_text_id = self.canvas.create_text(
            box_x, box_y, text="CLICK TO START", fill="white", font=("Courier", 30, "bold")
        )

        self.canvas.create_text(WIDTH//2, 650, text="[ ARROWS TO MOVE ]   [ SPACE TO SHOOT ]", fill="gray", font=("Consolas", 14))

    def animate(self):
        if not self.running: return

        # 1. Move Stars
        for star in self.stars:
            self.canvas.move(star['id'], 0, star['speed'])
            
            coords = self.canvas.coords(star['id'])
            if coords: 
                if coords[1] > HEIGHT:
                    new_x = random.randint(0, WIDTH)
                    self.canvas.coords(star['id'], new_x, -5, new_x+star['size'], -5+star['size'])

        # 2. Pulse Text
        self.pulse_alpha += self.pulse_direction
        if self.pulse_alpha > 20: self.pulse_direction = -1
        if self.pulse_alpha < 0: self.pulse_direction = 1
        
        if self.pulse_alpha > 10:
            self.canvas.itemconfig(self.start_text_id, fill="white")
        else:
            self.canvas.itemconfig(self.start_text_id, fill="#aaaaaa")

        self.root.after(30, self.animate)

    def on_hover(self, event):
        x, y = event.x, event.y
        if 300 < x < 700 and 400 < y < 500:
            self.canvas.itemconfig(self.play_btn_id, outline="white", fill="#2a0040")
            self.canvas.config(cursor="hand2")
        else:
            self.canvas.itemconfig(self.play_btn_id, outline=NEON_CYAN, fill="#110022")
            self.canvas.config(cursor="arrow")

    def on_click(self, event):
        x, y = event.x, event.y
        if 300 < x < 700 and 400 < y < 500:
            self.start_game()

    def start_game(self):
        self.running = False
        self.root.destroy()
        try:
            subprocess.Popen([sys.executable, "game.py"])
        except Exception as e:
            print(e)

    def quit_game(self):
        self.running = False
        self.root.quit()
        sys.exit()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SpaceInvadersMenu()
    app.run()