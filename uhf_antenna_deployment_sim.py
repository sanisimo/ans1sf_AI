"""Virtual-time model of the 2U UHF antenna deployment logic (MCU + UHF transceiver)."""

WIRES = {1: ("A1", "B1"), 2: ("A2", "B2")}
RODS_BY_WIRE = {1: (1, 2), 2: (3, 4)}
BURN_THRESHOLD_S = 10  # assumed minimum on-time of one resistor to cut its wire; confirm with design

MCU_DELAY_S = 120
UHF_DELAY_S = 300
UHF_LOOPS = 4
UHF_NO_COMM_TIMEOUT_S = 120
UHF_LOOP_PAUSE_S = 5
MAX_BOOT_CNT_ANT = 100
MAX_BOOT_CNT_UHF = 150


class Clock:
    def __init__(self):
        self.now = 0

    def sleep(self, seconds):
        self.now += seconds

    def sleep_until(self, t):
        self.now = max(self.now, t)


class Antenna:
    def __init__(self, clock, faulty_resistors=(), gpo_fault=False):
        self.clock = clock
        self.faulty = set(faulty_resistors)
        self.gpo_fault = gpo_fault
        self.events = []  # (time, resistor, "ON"/"OFF")
        self.runs = []  # (start time, source)
        self.on_time = {r: 0 for pair in WIRES.values() for r in pair}
        self._on_since = {}

    def _set(self, resistor, on):
        if resistor in self.faulty:
            return
        t = self.clock.now
        self.events.append((t, resistor, "ON" if on else "OFF"))
        if on:
            self._on_since[resistor] = t
        else:
            self.on_time[resistor] += t - self._on_since.pop(resistor)

    def run_algorithm(self, source):
        """A on, +5 s B on, +5 s A off, +5 s B off. source: 'MCU', 'MCU-by-UHF' or 'GPO'."""
        self.runs.append((self.clock.now, source))
        drive = not (source == "GPO" and self.gpo_fault)

        def step(resistors, on):
            if drive:
                for r in resistors:
                    self._set(r, on)

        step(("A1", "A2"), True)
        self.clock.sleep(5)
        step(("B1", "B2"), True)
        self.clock.sleep(5)
        step(("A1", "A2"), False)
        self.clock.sleep(5)
        step(("B1", "B2"), False)

    def wire_cut(self, wire):
        return any(self.on_time[r] >= BURN_THRESHOLD_S for r in WIRES[wire])

    @property
    def released_rods(self):
        return sorted(rod for w, rods in RODS_BY_WIRE.items() if self.wire_cut(w) for rod in rods)

    @property
    def deployed(self):
        return len(self.released_rods) == 4

    def on_time_of(self, resistor):
        return self.on_time[resistor]

    def event_times(self, resistor, state):
        return [t for t, r, s in self.events if r == resistor and s == state]


class AntennaMCU:
    def __init__(self, antenna, boot_cnt=0, robust_flag=1, healthy=True):
        self.antenna = antenna
        self.boot_cnt = boot_cnt
        self.robust_flag = robust_flag
        self.healthy = healthy

    def run(self, boot_time=0):
        # Assumption: the whole routine is gated by the boot counter (diagram's alt box is ambiguous).
        if not self.healthy or self.boot_cnt >= MAX_BOOT_CNT_ANT:
            return
        a = self.antenna
        a.clock.sleep_until(boot_time + MCU_DELAY_S)
        if self.robust_flag == 1:
            self.robust_flag = 0
        elif a.deployed:
            return
        a.run_algorithm("MCU")
        if a.deployed:
            return
        a.run_algorithm("MCU")


class UHFTransceiver:
    def __init__(self, antenna, mcu, boot_cnt=0):
        self.antenna = antenna
        self.mcu = mcu
        self.boot_cnt = boot_cnt

    def run(self, boot_time=0):
        if self.boot_cnt >= MAX_BOOT_CNT_UHF:
            return
        a = self.antenna
        a.clock.sleep_until(boot_time + UHF_DELAY_S)
        for loop in range(UHF_LOOPS):
            waited = 0
            while True:
                if a.deployed:
                    return
                if self.mcu.healthy:
                    a.run_algorithm("MCU-by-UHF" if loop % 2 == 0 else "GPO")
                    if a.deployed:
                        return
                    break
                a.clock.sleep(1)
                waited += 1
                if waited >= UHF_NO_COMM_TIMEOUT_S:
                    a.run_algorithm("GPO")
                    if a.deployed:
                        return
                    break
            a.clock.sleep(UHF_LOOP_PAUSE_S)
