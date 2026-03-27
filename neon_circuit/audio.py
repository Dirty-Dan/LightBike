"""Procedural retro audio for Neon Circuit."""

from __future__ import annotations

import math
import struct
from typing import Dict

import pygame

from .config import SOUND_PRESETS


class AudioManager:
    """Synthesizes and plays simple arcade-style audio effects."""

    def __init__(self) -> None:
        self.enabled = True
        self.sample_rate = 44_100
        self._loop_sounds: Dict[str, pygame.mixer.Sound] = {}
        self._sfx: Dict[str, pygame.mixer.Sound] = {}
        self._hum_channels: Dict[int, pygame.mixer.Channel] = {}
        self._init_mixer()
        if self.enabled:
            self._build_sounds()

    def _init_mixer(self) -> None:
        try:
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
        except pygame.error:
            self.enabled = False

    def _build_sounds(self) -> None:
        for name in SOUND_PRESETS:
            if name == "Classic Synth":
                self._loop_sounds[name] = self._build_loop(base_freq=170, mod_freq=3, depth=0.20, saw_mix=0.3)
            elif name == "Deep Engine":
                self._loop_sounds[name] = self._build_loop(base_freq=105, mod_freq=2, depth=0.18, saw_mix=0.5)
            else:
                self._loop_sounds[name] = self._build_loop(base_freq=240, mod_freq=8, depth=0.25, saw_mix=0.7)

        self._sfx["menu_move"] = self._build_burst(440, duration=0.04, decay=18)
        self._sfx["menu_select"] = self._build_burst(740, duration=0.07, decay=12)
        self._sfx["crash"] = self._build_noise_burst(duration=0.18)
        self._sfx["win"] = self._build_win_chime()

    def _build_loop(self, base_freq: float, mod_freq: float, depth: float, saw_mix: float) -> pygame.mixer.Sound:
        duration = 0.25
        count = int(duration * self.sample_rate)
        frames = bytearray()
        for i in range(count):
            t = i / self.sample_rate
            mod = 1 + depth * math.sin(2 * math.pi * mod_freq * t)
            freq = base_freq * mod
            sine = math.sin(2 * math.pi * freq * t)
            saw = 2 * ((freq * t) % 1.0) - 1
            sample = 0.55 * ((1 - saw_mix) * sine + saw_mix * saw)
            frames.extend(struct.pack("<h", int(sample * 32767)))
        return pygame.mixer.Sound(buffer=bytes(frames))

    def _build_burst(self, freq: float, duration: float, decay: float) -> pygame.mixer.Sound:
        count = int(duration * self.sample_rate)
        frames = bytearray()
        for i in range(count):
            t = i / self.sample_rate
            env = math.exp(-decay * t)
            sample = math.sin(2 * math.pi * freq * t) * env * 0.7
            frames.extend(struct.pack("<h", int(sample * 32767)))
        return pygame.mixer.Sound(buffer=bytes(frames))

    def _build_noise_burst(self, duration: float) -> pygame.mixer.Sound:
        count = int(duration * self.sample_rate)
        frames = bytearray()
        for i in range(count):
            t = i / self.sample_rate
            env = math.exp(-18 * t)
            noise = math.sin(2 * math.pi * (210 + 780 * (1 - env)) * t)
            sample = noise * env * 0.9
            frames.extend(struct.pack("<h", int(sample * 32767)))
        return pygame.mixer.Sound(buffer=bytes(frames))

    def _build_win_chime(self) -> pygame.mixer.Sound:
        notes = [523.25, 659.26, 783.99, 1046.5]
        note_dur = 0.08
        count = int(len(notes) * note_dur * self.sample_rate)
        frames = bytearray()
        for i in range(count):
            t = i / self.sample_rate
            note_idx = min(len(notes) - 1, int(t / note_dur))
            note_time = t - note_idx * note_dur
            env = math.exp(-11 * note_time)
            sample = math.sin(2 * math.pi * notes[note_idx] * note_time) * env * 0.8
            frames.extend(struct.pack("<h", int(sample * 32767)))
        return pygame.mixer.Sound(buffer=bytes(frames))

    def menu_move(self) -> None:
        self.play_sfx("menu_move")

    def menu_select(self) -> None:
        self.play_sfx("menu_select")

    def play_sfx(self, name: str) -> None:
        if not self.enabled:
            return
        sound = self._sfx.get(name)
        if sound:
            sound.play()

    def start_bike_hum(self, player_id: int, profile: str) -> None:
        if not self.enabled:
            return
        self.stop_bike_hum(player_id)
        sound = self._loop_sounds.get(profile)
        if sound:
            channel = pygame.mixer.find_channel(True)
            channel.set_volume(0.28)
            channel.play(sound, loops=-1)
            self._hum_channels[player_id] = channel

    def stop_bike_hum(self, player_id: int) -> None:
        channel = self._hum_channels.pop(player_id, None)
        if channel:
            channel.stop()

    def stop_all_hums(self) -> None:
        for pid in list(self._hum_channels):
            self.stop_bike_hum(pid)
