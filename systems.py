"""游戏规则系统。

这里处理射击、实体更新、道具、伤害和碰撞。主流程负责调度，具体规则放在这里。
"""

import datetime
import math
import random

import pygame

from constants import (
    BULLET_STREAM_SPACING,
    RAPID_FIRE_CD_MULTIPLIER,
    REPAIR_HEAL_AMOUNT,
    SCORE_POWERUP_RATIO,
    SHIELD_POWERUP_AMOUNT,
)
from entities import Bullet, Enemy, PowerUp


def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


class GameSystems:
    """游戏规则门面。

    主循环只调用这里的公开方法；具体射击、生成、道具和碰撞细节都集中在本类。
    """

    def __init__(self, game):
        self.game = game

    def player_shoot(self, player, bullets):
        """根据玩家当前弹道数生成子弹。"""
        if player.try_shoot():
            bullet_x = player.x + player.W // 2
            bullet_y = player.y + 30
            center_offset = (player.bullet_streams - 1) / 2
            for index in range(player.bullet_streams):
                offset_x = (index - center_offset) * BULLET_STREAM_SPACING
                bullets.append(Bullet(bullet_x + offset_x, bullet_y, self.game))

    def try_spawn_enemy(self, spawn_timer, spawn_interval, enemies):
        """推进生成计时器，达到间隔时生成一个新陨石。"""
        spawn_timer += 1
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            if len(enemies) < self.game.MAX_ENEMIES:
                enemies.append(Enemy(self.game))
        return spawn_timer

    def update_entities(self, bullets, enemies, particles, player):
        """更新子弹、陨石和粒子，并清理离屏或死亡对象。"""
        bullets[:] = [b for b in bullets if not b.update()]
        runtime_tools = getattr(self.game, "runtime_tools", None)
        update_enemies = True
        speed_multiplier = 1.0
        if runtime_tools and hasattr(runtime_tools, "get_enemy_update_settings"):
            update_enemies, speed_multiplier = runtime_tools.get_enemy_update_settings()
        if update_enemies:
            enemies[:] = [e for e in enemies if not e.update(speed_multiplier)]

        particles = self.game.effects.update_particles(particles)
        if len(particles) > self.game.MAX_PARTICLES:
            particles = particles[-self.game.MAX_PARTICLES:]

        return particles

    def update_powerups(self, powerups):
        """更新道具位置，并移除掉出屏幕的道具。"""
        powerups[:] = [powerup for powerup in powerups if not powerup.update()]

    def drop_powerup(self, powerups, enemy, difficulty):
        """按陨石大小和难度决定是否掉落道具。

        陨石越大掉率越高、可掉落道具池越丰富；难度越高掉率略微降低。
        """
        if powerups is None:
            return

        size_bonus = enemy.kind * 0.10
        difficulty_penalty = max(0, difficulty - 1) * 0.001
        drop_chance = min(0.80, max(0.10, 0.30 + size_bonus - difficulty_penalty))
        if random.random() > drop_chance:
            return

        pool_size = enemy.kind + 1
        powerup_kinds = ["score", "shield", "repair", "rapid_fire", "bullet_stream"][:pool_size]
        powerup_weights = [0.20, 0.20, 0.20, 0.20, 0.20][:pool_size]
        kind = random.choices(powerup_kinds, weights=powerup_weights, k=1)[0]
        powerup_image = self.game.POWERUP_IMAGES.get(kind)
        powerups.append(PowerUp(enemy.x + enemy.W // 2, enemy.y + enemy.H // 2, kind, image=powerup_image))

    def apply_powerup(self, player, powerup):
        """将道具效果应用到玩家身上。"""
        if powerup.kind == "repair":
            player.hp = min(player.actual_max_hp, player.hp + REPAIR_HEAL_AMOUNT)
            log(f"拾取维修道具：血量={player.hp}/{player.actual_max_hp}")
        elif powerup.kind == "score":
            score_bonus = int(player.score * SCORE_POWERUP_RATIO)
            player.score += score_bonus
            log(f"拾取加分道具：当前分数={player.score}")
        elif powerup.kind == "shield":
            player.shield = min(player.max_shield, player.shield + SHIELD_POWERUP_AMOUNT)
            log(f"拾取护盾道具：护盾={player.shield}/{player.max_shield}")
        elif powerup.kind == "rapid_fire":
            player.shoot_cd *= RAPID_FIRE_CD_MULTIPLIER
            log(f"拾取射速道具：射击冷却={player.shoot_cd:.2f} 帧")
        elif powerup.kind == "bullet_stream":
            player.bullet_streams += 1
            log(f"拾取弹道道具：当前弹道数={player.bullet_streams}")

    def handle_powerup_collisions(self, powerups, player):
        """检测玩家是否拾取道具。"""
        player_rect = pygame.Rect(int(player.x), int(player.y), player.W, player.H)
        for powerup in powerups[:]:
            if player_rect.colliderect(powerup.rect):
                self.apply_powerup(player, powerup)
                powerups.remove(powerup)

    def damage_player(self, player, enemy):
        """结算陨石撞击玩家造成的伤害、护盾抵消和无敌帧。"""
        damage_min, damage_max = self.game.METEORITE_DAMAGE_RANGES[enemy.kind]
        damage = random.randint(damage_min, damage_max)
        original_damage = damage

        if player.shield > 0:
            absorbed = min(player.shield, damage)
            player.shield -= absorbed
            damage -= absorbed
            log(f"护盾抵消伤害：{absorbed}，剩余护盾={player.shield}")

        player.hp = max(0, player.hp - damage)

        max_reduce_max_hp = player.max_hp * 3 / 4
        player.reduce_max_hp = min(max_reduce_max_hp, player.reduce_max_hp + original_damage * 0.2)
        player.actual_max_hp = player.max_hp - player.reduce_max_hp
        player.hp = min(player.hp, player.actual_max_hp)

        if player.hp <= 0:
            player.lives -= 1
            if player.lives > 0:
                player.reduce_max_hp = 0
                player.actual_max_hp = player.max_hp
                player.hp = player.actual_max_hp
            player.invincible = 120
            player.can_shoot = False
            return original_damage, True

        player.invincible = 45
        return original_damage, False

    def handle_collisions(self, bullets, enemies, particles, player, difficulty=1, powerups=None):
        """处理子弹打陨石、陨石碎裂、道具掉落，以及玩家被陨石撞击。"""
        game = self.game
        clamped_difficulty = min(max(difficulty, 1), 12)
        spawn_probability = min(0.9, 0.5 + (clamped_difficulty - 1) * 0.1)
        piece_multiplier = 1 + min(1.5, (clamped_difficulty - 1) * 0.1)

        for b in bullets[:]:
            for e in enemies[:]:
                expanded_e_x = e.x - 5
                expanded_e_y = e.y - 5
                expanded_e_w = e.W + 10
                expanded_e_h = e.H + 10

                if not (
                    b.x + b.W > expanded_e_x
                    and b.x < expanded_e_x + expanded_e_w
                    and b.y + b.H > expanded_e_y
                    and b.y < expanded_e_y + expanded_e_h
                ):
                    continue

                bullet_cx = b.x + b.W // 2
                bullet_cy = b.y + b.H // 2
                collision_x = bullet_cx
                collision_y = bullet_cy
                hit_confirmed = False

                if e.meteorite_img:
                    try:
                        center_x = e.x + e.W // 2
                        center_y = e.y + e.H // 2

                        if hasattr(e, 'rotated_mask') and e.rotated_mask is not None and e.rotated_rect is not None:
                            rotated_mask = e.rotated_mask
                            rotated_rect = e.rotated_rect
                        else:
                            sc = game.SIZE_SCALE[e.kind]
                            img_width, img_height = e.meteorite_img.get_size()
                            scaled_img = pygame.transform.smoothscale(
                                e.meteorite_img,
                                (int(img_width * sc), int(img_height * sc)),
                            )
                            rotation_deg = int(e.rotation * 180 / math.pi)
                            rotated_img = pygame.transform.rotate(scaled_img, rotation_deg)
                            rotated_mask = pygame.mask.from_surface(rotated_img)
                            rotated_rect = rotated_img.get_rect(center=(center_x, center_y))

                        offset_x = int(b.x) - rotated_rect.left
                        offset_y = int(b.y) - rotated_rect.top
                        bullet_mask = getattr(b, "mask", game.BULLET_MASK)
                        if rotated_mask.overlap(bullet_mask, (offset_x, offset_y)):
                            hit_confirmed = True
                    except (pygame.error, ValueError, MemoryError) as ex:
                        log(f"子弹-陨石像素遮罩碰撞失败 (种类{e.kind}): {ex}")
                        center_x = e.x + e.W // 2
                        center_y = e.y + e.H // 2
                        dist = math.sqrt((bullet_cx - center_x)**2 + (bullet_cy - center_y)**2)
                        if dist < max(e.W, e.H) // 2:
                            hit_confirmed = True
                else:
                    center_x = e.x + e.W // 2
                    center_y = e.y + e.H // 2
                    dist = math.sqrt((bullet_cx - center_x)**2 + (bullet_cy - center_y)**2)
                    hit_confirmed = dist < max(e.W, e.H) // 2

                if hit_confirmed:
                    if b in bullets:
                        bullets.remove(b)
                    e.hp -= 1
                    particles += game.effects.make_explosion(collision_x, collision_y, n=8, r_range=(2, 6))

                    if e.hp <= 0:
                        particles += game.effects.make_meteorite_explosion(e)
                        player.score += game.SIZE_SCORE[e.kind]
                        self.drop_powerup(powerups, e, difficulty)

                        if e.kind > 1 and random.random() < spawn_probability:
                            self._spawn_meteorite_fragments(enemies, e, piece_multiplier)

                        if e in enemies:
                            enemies.remove(e)
                break

        if not getattr(player, "god_mode", False) and player.invincible == 0:
            self._handle_player_meteorite_collisions(enemies, particles, player)

        return particles

    def _spawn_meteorite_fragments(self, enemies, enemy, piece_multiplier):
        """把大陨石拆成更小的陨石碎片。"""
        base_max_pieces = int(min(4, enemy.kind * 1.5))
        base_min_pieces = max(1, enemy.kind - 1)
        max_pieces = max(1, min(4, int(base_max_pieces * piece_multiplier)))
        min_pieces = max(1, min(max_pieces, int(base_min_pieces * piece_multiplier * 0.6)))
        if min_pieces > max_pieces:
            min_pieces = max_pieces

        for _ in range(random.randint(min_pieces, max_pieces)):
            new_kind = random.randint(0, enemy.kind - 1)
            new_enemy = Enemy(self.game, kind=new_kind, meteorite_img=enemy.meteorite_img)
            new_enemy.x = enemy.x + random.randint(-enemy.W//4, enemy.W//4)
            new_enemy.y = enemy.y + random.randint(-enemy.H//4, enemy.H//4)

            angle = random.uniform(0, math.pi * 2)
            original_speed = math.sqrt(enemy.vx**2 + enemy.vy**2)
            new_speed = original_speed * 2
            new_enemy.vx = new_speed * math.cos(angle)
            new_enemy.vy = new_speed * math.sin(angle)
            enemies.append(new_enemy)

    def _handle_player_meteorite_collisions(self, enemies, particles, player):
        """检测陨石与玩家的像素碰撞，异常时回退到距离检测。"""
        game = self.game
        for e in enemies[:]:
            if not (
                player.x + player.W > e.x
                and player.x < e.x + e.W
                and player.y + player.H > e.y
                and player.y < e.y + e.H
            ):
                continue

            if e.meteorite_img:
                try:
                    if hasattr(e, 'rotated_mask') and e.rotated_mask is not None and e.rotated_rect is not None:
                        rotated_mask = e.rotated_mask
                        rotated_rect = e.rotated_rect
                    else:
                        sc = game.SIZE_SCALE[e.kind]
                        img_width, img_height = e.meteorite_img.get_size()
                        scaled_img = pygame.transform.smoothscale(
                            e.meteorite_img,
                            (int(img_width * sc), int(img_height * sc)),
                        )
                        rotation_deg = int(e.rotation * 180 / math.pi)
                        rotated_img = pygame.transform.rotate(scaled_img, rotation_deg)
                        rotated_mask = pygame.mask.from_surface(rotated_img)
                        rotated_rect = rotated_img.get_rect(center=(e.x + e.W // 2, e.y + e.H // 2))

                    offset_x = int(player.x) - int(rotated_rect.left)
                    offset_y = int(player.y) - int(rotated_rect.top)
                    collision_detected = game.PLAYER_MASK.overlap(rotated_mask, (offset_x, offset_y))

                    if collision_detected or self._player_near_enemy(player, e):
                        self._resolve_player_hit(enemies, particles, player, e)
                        break
                except (pygame.error, ValueError, MemoryError, IndexError) as ex:
                    log(f"玩家-陨石碰撞异常 (种类{e.kind}): {ex}, 使用距离检测")
                    if self._player_near_enemy(player, e):
                        self._resolve_player_hit(enemies, particles, player, e)
                        break

    def _player_near_enemy(self, player, enemy):
        """距离碰撞兜底，避免遮罩异常时玩家完全不受撞击。"""
        center_x = enemy.x + enemy.W // 2
        center_y = enemy.y + enemy.H // 2
        player_cx = player.x + player.W // 2
        player_cy = player.y + player.H // 2
        dist = math.sqrt((player_cx - center_x)**2 + (player_cy - center_y)**2)
        return dist < max(enemy.W, enemy.H) * 0.75

    def _resolve_player_hit(self, enemies, particles, player, enemy):
        """统一处理玩家被某个陨石击中的爆炸、扣血和移除陨石。"""
        explosion_x = enemy.x + enemy.W // 2
        explosion_y = enemy.y + enemy.H // 2
        particles += self.game.effects.make_explosion(explosion_x, explosion_y, n=40, r_range=(8, 20))
        damage, died = self.damage_player(player, enemy)
        log(
            f"玩家被 {enemy.kind} 级陨石击中：扣除 {damage} 点血量，"
            f"当前血量={player.hp}/{player.max_hp}，剩余命数={player.lives}"
        )
        if enemy in enemies:
            enemies.remove(enemy)
