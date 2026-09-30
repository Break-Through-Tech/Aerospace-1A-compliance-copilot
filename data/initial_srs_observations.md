# Team Aerospace 1A Starhawk Space Mission SRS Observations

### 1. What information does this document contain?
Answer: This Starhawk Space Mission SRS document outlines, covers and stresses on the following:-

1. Introduction & Overview: Defines the scope for the Starhawk SFMC software, its major hardware/subsystem interfaces, and its 5 operational modes (Standby, Manual Flight, Autopilot, Combat, Emergency).

2. External Interfaces: Describes interactions between the SFMC, pilot cockpit controls/displays, and core subsystems (Navigation, Propulsion, Weapons, Defensive, Communications).

3. Functional Software Requirements (SFMC-REQ-001 through 030): Specific rules governing Navigation updates, Fuel warnings, Targeting/Weapons authorization, Threat priority/Shields, Fleet communications, and Fault logging.

4–9. Non-Functional & Operational Requirements:

Emergency Operations: Automatic safe routing and life-support prioritization.

Performance: Boot time (<30s), display refresh rate (10 Hz), and 72-hour operation.

Reliability: Fault recovery and zero mission-critical crashes.

Data & Security: Mission event logging, pilot authentication, and cyberattack prevention.

Constraints: Target hardware platform and network interface rules.

10. Requirement Traceability: Maps software requirements back to High-Level Mission Needs (MN-01 to MN-10).

11. Open Items: Lists 10 unresolved technical definitions and criteria requiring further development (e.g., criteria for friendly vs. hostile targets, cybersecurity standards).



### 2. What information would a developer obtain from this document?
Answer: From this document, a software developer would obtain the target system's **architectural boundaries, operational requirements, system constraints, high-level business rules, and technical gaps** needed to begin design and implementation.

Specifically, a developer learns the following details:

### 1. System Architecture & Scope

* **Target Hardware Platform:** The software must run on the *Starhawk Flight Computer* and interface across the *Starhawk spacecraft data network*. Hardware design itself is out of scope.
* **System Boundaries:** The SFMC acts as a central hub interfacing with 7 external subsystems: Pilot Display/Controls, Navigation, Propulsion, Weapons, Defensive, Communications, and Vehicle Health Monitoring.
* **State Machine / Operating Modes:** The software must support 5 distinct states: *Standby*, *Manual Flight*, *Autopilot*, *Combat*, and *Emergency*.

### 2. Concrete Functional & Business Logic

* **Timing & Refresh Rates:** Navigation position display updates every $\le 500\text{ ms}$, primary display flight information updates at least $10\text{ Hz}$ ($10\text{ times/sec}$), and system fault alerts must trigger within $1\text{ second}$.
* **Conditional Logic & Hard Rules:**
* Trigger a low-fuel warning at $< 15\%$ fuel capacity and a critical audio alert at $< 5\%$.
* Hard safety interlock: Block weapons from firing if pilot authorization is missing or if targeted at a friendly spacecraft.
* Combat mode automatically triggers defensive shields.
* Operational fail-safes: The pilot must be able to manually override automatic flight controls at any time.


* **Logging Protocols:** Must log fault IDs, affected systems, timestamps, and descriptions, along with mode changes, pilot commands, and weapons fire events into non-volatile storage.

### 3. Non-Functional & Quality Attributes

* **Performance:** Maximum boot/startup time of $30\text{ seconds}$, continuous operational capability up to $72\text{ hours}$, and zero command latency.
* **Reliability & Resilience:** Fault-tolerant architecture requiring automatic recovery without data loss, zero mission-critical crashes, and graceful degradation if subsystems fail.
* **Security & Deployment:** Requires pilot identity authentication, message payload encryption, rejection of unauthorized external remote commands, and signature verification for over-the-air software updates.

### 4. Technical Gaps & Implementation Constraints (Section 11)

A developer would also discover **what *cannot* be implemented yet** due to missing definitions. The developer must seek clarification on 10 open items, including:

* Specific algorithms for cybersecurity and target classification (friendly vs. hostile).
* Quantitative thresholds for command response times, targeting accuracy, and mission log storage capacity.
* Formal mathematical definitions for "safe route", "critical fault", and "safe location" during emergency mode.

