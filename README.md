<img width="520" height="400" alt="image" src="https://github.com/user-attachments/assets/d2e690b2-27f5-4566-9f79-26046d5f1d7c" />

# Physics simulation
## this is pygame physics simulation. below will be main functions of the code
<br><br>

# Simulator Functions

## Object Creation
- `spawn_circle(position, radius=20, mass=1)`  
  Creates a circle at the given position.

- `spawn_rectangle(position, size=(40, 30), mass=1)`  
  Creates a rectangle.

- `spawn_triangle(position, size=40, mass=1)`  
  Creates an equilateral triangle.

- `spawn_pentagon(position, size=40, mass=1)`  
  Creates a regular pentagon.

- `clear_scene()`  
  Removes all dynamic shapes from the scene.

---

## Physics Controls
- **Explosion power slider** (top left, controlled with the mouse).  
- **Gravity slider** (from -1g to +1g).  

---

## keyboard Features
- **Pause (P)**  
  Stops the physics simulation. Press again to resume.

- **Recolor (K)**  
  Changes all dynamic shapes to random colors.

- **Wind (V)**  
  Periodically applies wind force to all bodies (left or right). Toggle with `V`.

- **Rain (D)**  
  Toggles a rain generator: small balls fall from the top.

- **Explosion (Space)**  
  Instantly creates an explosion at the center of the screen, with current slider power.

---

## Spawn Keys
- `1` — Spawn a circle.  
- `2` — Spawn a rectangle.  
- `3` — Spawn a triangle.  
- `4` — Spawn a pentagon.  
- `C` — Clear the scene.  
