import sys
import math
import random
import pygame
import pymunk
import pymunk.pygame_util

pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Physics Simulator")
clock = pygame.time.Clock()

space = pymunk.Space()
space.gravity = (0, 900)
space.damping = 0.99

static_body = pymunk.Body(body_type=pymunk.Body.STATIC)
floor = pymunk.Segment(static_body, (0, height - 50), (width, height - 50), 5)
floor.friction = 1.0
ceiling = pymunk.Segment(static_body, (0, 0), (width, 0), 5)
ceiling.friction = 1.0
left_wall = pymunk.Segment(static_body, (0, 0), (0, height), 5)
left_wall.friction = 1.0
right_wall = pymunk.Segment(static_body, (width, 0), (width, height), 5)
right_wall.friction = 1.0
space.add(static_body, floor, ceiling, left_wall, right_wall)

slider_min, slider_max = 1, 10
slider_value = 3
base_explosion = 1500
explosion_radius = 100

gravity_min, gravity_max = -1, 1
gravity_value = 1

mouse_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
dragged_joint = None
dragged_shape = None

slider_width = 200
slider_height = 10
slider_x = 50
slider_y = 20
slider_dragging = False

gravity_slider_x = 50
gravity_slider_y = 60
gravity_slider_dragging = False

font = pygame.font.SysFont("Arial", 16)

paused = False
wind_enabled = False
wind_direction = 1
wind_timer = 0.0
wind_period = 3.0
wind_strength = 800.0

rain_enabled = False
rain_timer = 0.0
rain_interval = 0.08

draw_options = pymunk.pygame_util.DrawOptions(screen)

def random_color():
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

def spawn_circle(position, radius=20, mass=1):
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = position
    shape = pymunk.Circle(body, radius)
    shape.friction = 0.5
    shape.elasticity = 0.8
    shape.color = random_color()
    space.add(body, shape)

def spawn_rectangle(position, size=(40, 30), mass=1):
    w, h = size
    moment = pymunk.moment_for_box(mass, (w, h))
    body = pymunk.Body(mass, moment)
    body.position = position
    shape = pymunk.Poly.create_box(body, (w, h))
    shape.friction = 0.5
    shape.elasticity = 0.8
    shape.color = random_color()
    space.add(body, shape)

def spawn_triangle(position, size=40, mass=1):
    s = size
    points = [(-s/2, s/2), (s/2, s/2), (0, -s/2)]
    moment = pymunk.moment_for_poly(mass, points)
    body = pymunk.Body(mass, moment)
    body.position = position
    shape = pymunk.Poly(body, points)
    shape.friction = 0.5
    shape.elasticity = 0.8
    shape.color = random_color()
    space.add(body, shape)

def spawn_pentagon(position, size=30, mass=1):
    points = []
    for i in range(5):
        angle = 2 * math.pi * i / 5 - math.pi / 2
        x = size * math.cos(angle)
        y = size * math.sin(angle)
        points.append((x, y))
    moment = pymunk.moment_for_poly(mass, points)
    body = pymunk.Body(mass, moment)
    body.position = position
    shape = pymunk.Poly(body, points)
    shape.friction = 0.5
    shape.elasticity = 0.8
    shape.color = random_color()
    space.add(body, shape)

def clear_scene():
    bodies_to_remove = [b for b in space.bodies if b.body_type == pymunk.Body.DYNAMIC]
    for b in bodies_to_remove:
        for s in b.shapes[:]:
            if s in space.shapes:
                space.remove(s)
        if b in space.bodies:
            space.remove(b)

def apply_explosion(center, power, radius):
    for body in list(space.bodies):
        if body.body_type != pymunk.Body.DYNAMIC:
            continue
        distance = body.position.get_distance(center)
        if distance < radius:
            if distance == 0:
                distance = 0.1
            impulse_magnitude = power * (1 - (distance / radius))
            direction = (body.position - center)
            if direction.length == 0:
                direction = pymunk.Vec2d(random.random() - 0.5, random.random() - 0.5).normalized()
            else:
                direction = direction.normalized()
            impulse = direction * impulse_magnitude
            border_margin = 150
            pos = body.position
            if pos.x < border_margin and impulse.x < 0:
                scale = pos.x / border_margin
                impulse = pymunk.Vec2d(impulse.x * scale, impulse.y)
            elif pos.x > width - border_margin and impulse.x > 0:
                scale = (width - pos.x) / border_margin
                impulse = pymunk.Vec2d(impulse.x * scale, impulse.y)
            if pos.y < border_margin and impulse.y < 0:
                scale = pos.y / border_margin
                impulse = pymunk.Vec2d(impulse.x, impulse.y * scale)
            elif pos.y > height - border_margin and impulse.y > 0:
                scale = (height - pos.y) / border_margin
                impulse = pymunk.Vec2d(impulse.x, impulse.y * scale)
            max_impulse = slider_value * 1000
            if impulse.length > max_impulse:
                impulse = impulse.normalized() * max_impulse
            body.apply_impulse_at_local_point(impulse)

def recolor_all():
    for s in space.shapes:
        if hasattr(s, "body") and s.body.body_type == pymunk.Body.DYNAMIC:
            s.color = random_color()

def spawn_rain_drop():
    x = random.uniform(30, width - 30)
    pos = pymunk.pygame_util.from_pygame((x, 10), screen)
    spawn_circle(pos, radius=5, mass=0.2)

def draw_shapes_custom():
    for shape in space.shapes:
        if isinstance(shape, pymunk.Circle):
            body = shape.body
            try:
                offset = shape.offset
                p = body.position + offset.rotated(body.angle)
            except Exception:
                p = body.position
            p = pymunk.pygame_util.to_pygame(p, screen)
            color = shape.color if hasattr(shape, "color") else (0, 0, 0)
            pygame.draw.circle(screen, color, (int(p[0]), int(p[1])), int(shape.radius))
        elif isinstance(shape, pymunk.Poly):
            body = shape.body
            vertices = [body.local_to_world(v) for v in shape.get_vertices()]
            vertices = [pymunk.pygame_util.to_pygame(v, screen) for v in vertices]
            color = shape.color if hasattr(shape, "color") else (0, 0, 0)
            if len(vertices) >= 3:
                pygame.draw.polygon(screen, color, vertices)
        elif isinstance(shape, pymunk.Segment):
            a = pymunk.pygame_util.to_pygame(shape.a, screen)
            b = pymunk.pygame_util.to_pygame(shape.b, screen)
            pygame.draw.line(screen, (0, 0, 0), a, b, int(shape.radius * 2))

running = True
while running:
    dt = 1.0 / 60.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                slider_rect = pygame.Rect(slider_x, slider_y - 5, slider_width, slider_height + 10)
                gravity_slider_rect = pygame.Rect(gravity_slider_x, gravity_slider_y - 5, slider_width, slider_height + 10)
                if slider_rect.collidepoint(mouse_pos):
                    slider_dragging = True
                    relative_x = mouse_pos[0] - slider_x
                    fraction = relative_x / slider_width
                    slider_value = slider_min + fraction * (slider_max - slider_min)
                    slider_value = max(slider_min, min(slider_max, round(slider_value)))
                elif gravity_slider_rect.collidepoint(mouse_pos):
                    gravity_slider_dragging = True
                    relative_x = mouse_pos[0] - gravity_slider_x
                    fraction = relative_x / slider_width
                    gravity_value = gravity_min + fraction * (gravity_max - gravity_min)
                    gravity_value = max(gravity_min, min(gravity_max, round(gravity_value, 2)))
                    space.gravity = (0, gravity_value * 900)
                else:
                    pos = pymunk.pygame_util.from_pygame(mouse_pos, screen)
                    hit = space.point_query_nearest(pos, 5, pymunk.ShapeFilter())
                    if hit:
                        dragged_shape = hit.shape
                        mouse_body.position = pos
                        dragged_joint = pymunk.PivotJoint(mouse_body, dragged_shape.body, (0, 0), dragged_shape.body.world_to_local(pos))
                        dragged_joint.max_force = 50000
                        space.add(dragged_joint)
            elif event.button == 3:
                pos = pymunk.pygame_util.from_pygame(pygame.mouse.get_pos(), screen)
                current_explosion_power = slider_value * base_explosion
                apply_explosion(pos, current_explosion_power, explosion_radius)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                slider_dragging = False
                gravity_slider_dragging = False
                if dragged_joint is not None:
                    try:
                        space.remove(dragged_joint)
                    except Exception:
                        pass
                    dragged_joint = None
                    dragged_shape = None

        elif event.type == pygame.MOUSEMOTION:
            if slider_dragging:
                mouse_pos = pygame.mouse.get_pos()
                relative_x = mouse_pos[0] - slider_x
                fraction = relative_x / slider_width
                slider_value = slider_min + fraction * (slider_max - slider_min)
                slider_value = max(slider_min, min(slider_max, round(slider_value)))
            elif gravity_slider_dragging:
                mouse_pos = pygame.mouse.get_pos()
                relative_x = mouse_pos[0] - gravity_slider_x
                fraction = relative_x / slider_width
                gravity_value = gravity_min + fraction * (gravity_max - gravity_min)
                gravity_value = max(gravity_min, min(gravity_max, round(gravity_value, 2)))
                space.gravity = (0, gravity_value * 900)
            elif dragged_joint is not None:
                pos = pymunk.pygame_util.from_pygame(pygame.mouse.get_pos(), screen)
                mouse_body.position = pos

        elif event.type == pygame.KEYDOWN:
            pos = pymunk.pygame_util.from_pygame(pygame.mouse.get_pos(), screen)
            if event.key == pygame.K_1:
                spawn_circle(pos)
            elif event.key == pygame.K_2:
                spawn_rectangle(pos)
            elif event.key == pygame.K_3:
                spawn_triangle(pos)
            elif event.key == pygame.K_4:
                spawn_pentagon(pos)
            elif event.key == pygame.K_c:
                clear_scene()
            elif event.key == pygame.K_p:
                paused = not paused
            elif event.key == pygame.K_k:
                recolor_all()
            elif event.key == pygame.K_v:
                wind_enabled = not wind_enabled
                wind_timer = 0.0
            elif event.key == pygame.K_d:
                rain_enabled = not rain_enabled
                rain_timer = 0.0
            elif event.key == pygame.K_SPACE:
                center = pymunk.pygame_util.from_pygame((width // 2, height // 2), screen)
                current_explosion_power = slider_value * base_explosion
                apply_explosion(center, current_explosion_power, explosion_radius)

    if wind_enabled and not paused:
        wind_timer += dt
        if wind_timer >= wind_period:
            wind_timer = 0.0
            wind_direction *= -1
        for b in space.bodies:
            if b.body_type != pymunk.Body.DYNAMIC:
                continue
            f = (wind_direction * wind_strength * b.mass, 0)
            b.apply_force_at_local_point(f, (0, 0))

    if rain_enabled and not paused:
        rain_timer += dt
        while rain_timer >= rain_interval:
            rain_timer -= rain_interval
            spawn_rain_drop()

    screen.fill((255, 255, 255))
    draw_shapes_custom()

    pygame.draw.rect(screen, (200, 200, 200), (slider_x, slider_y, slider_width, slider_height))
    knob_x = slider_x + ((slider_value - slider_min) / (slider_max - slider_min)) * slider_width
    knob_y = slider_y + slider_height // 2
    pygame.draw.circle(screen, (100, 100, 250), (int(knob_x), int(knob_y)), 8)
    text = font.render(f"Explosion power: {slider_value}", True, (0, 0, 0))
    screen.blit(text, (slider_x, slider_y - 20))

    pygame.draw.rect(screen, (200, 200, 200), (gravity_slider_x, gravity_slider_y, slider_width, slider_height))
    g_knob_x = gravity_slider_x + ((gravity_value - gravity_min) / (gravity_max - gravity_min)) * slider_width
    g_knob_y = gravity_slider_y + slider_height // 2
    pygame.draw.circle(screen, (250, 100, 100), (int(g_knob_x), int(g_knob_y)), 8)
    text_g = font.render(f"Gravity: {gravity_value:.2f}g", True, (0, 0, 0))
    screen.blit(text_g, (gravity_slider_x, gravity_slider_y - 20))

    status_text = f"P:Pause({'ON' if paused else 'OFF'})  K:Recolor  V:Wind({'ON' if wind_enabled else 'OFF'})  D:Rain({'ON' if rain_enabled else 'OFF'})  Space:Explosion"
    status = font.render(status_text, True, (0, 0, 0))
    screen.blit(status, (50, height - 30))

    pygame.display.flip()

    if not paused:
        space.step(dt)

    clock.tick(60)

pygame.quit()
sys.exit()
